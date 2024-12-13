import aiohttp
import asyncio
from configparser import ConfigParser
import json
import os
import sys


# Main function to handle translation of an .srt file
async def translate_srt(file_path, target_language):
    """
    Translates an .srt file to the specified target language using OpenAI's API.

    Args:
        file_path (str): Path to the input .srt file.
        target_language (str): Language to translate the subtitles into.

    Returns:
        None
    """

    # Get the directory of the script to locate config.ini
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.ini")
    
    # Check for config.ini and prompt user for API key if missing
    if not os.path.exists(config_path):
        print("Config file not found. Please provide your OpenAI API key.")
        api_key = input("Enter your OpenAI API key: ").strip()
        
        # Create and save the config.ini file
        config = ConfigParser()
        config["openai"] = {"api_key": api_key}
        with open(config_path, "w") as config_file:
            config.write(config_file)
        print(f"API key saved to {config_path}")
    else:
        # Read the OpenAI API key from config.ini
        config = ConfigParser()
        config.read(config_path)
        if not config.has_option("openai", "api_key"):
            print("Error: API key not found in config.ini.")
            return
        api_key = config.get("openai", "api_key")

    # Define the system role prompt for the AI
    system_role = (
        f"You're a bot that takes subtitles blocks and translates them in {target_language}. "
        "Keep the subtitle number, the timeline and the eventual formatting unchanged. "
        "Don't add comments or remarks, just send the translated subtitle blocks."
    )

    # Validate the input file
    if not os.path.exists(file_path) or not file_path.endswith(".srt"):
        print("Invalid .srt file path.")
        return

    # Prepare the output file name
    base_name = os.path.splitext(file_path)[0]
    output_file = f"{base_name}.{target_language}.srt"
    if os.path.exists(output_file):
        os.remove(output_file)  # Remove existing output file if present

    # Read and split the input .srt file into subtitle blocks
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    subtitle_blocks = content.strip().split("\n\n")


    # Function to send requests to OpenAI's API
    async def send_request(messages):
        """
        Sends a conversation message to OpenAI's API.

        Args:
            messages (list): Conversation history including system, user, and assistant messages.

        Returns:
            str: The assistant's response (translated subtitles).
        """
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "gpt-4o-mini", # Change this to the OpenAI chat model you want to use
                "messages": messages,
            }
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload),
            ) as response:
                response.raise_for_status()  # Raise an exception for HTTP errors
                response_data = await response.json()
                return response_data["choices"][0]["message"]["content"]

    # Translate the subtitles in batches of 35 blocks
    batch_size = 35
    conversation = [{"role": "system", "content": system_role}]  # Initialize conversation with system prompt
    for i in range(0, len(subtitle_blocks), batch_size):
        batch = subtitle_blocks[i:i + batch_size]  # Extract the current batch of subtitles
        user_message = "\n\n".join(batch)  # Combine the batch into a single string
        print(f"Translating batch {i // batch_size + 1}...")

        try:
            # Add the user's request to the conversation
            conversation.append({"role": "user", "content": user_message})

            # Send the conversation to the AI and get the assistant's response
            assistant_response = await send_request(conversation)

            # Add the assistant's response to the conversation for continuity
            conversation.append({"role": "assistant", "content": assistant_response})

            # Append the translated batch to the output file
            with open(output_file, "a", encoding="utf-8") as out_file:
                out_file.write(assistant_response + "\n\n")

        except Exception as e:
            print(f"Error translating batch {i // batch_size + 1}: {e}")
            break

    print(f"Translation complete. File saved at: {output_file}")


# Entry point for the script
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 translate_srt.py path/to/file.srt destination_language")
    else:
        input_file = sys.argv[1]
        dest_language = sys.argv[2]
        asyncio.run(translate_srt(input_file, dest_language))