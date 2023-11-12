from PIL import Image, ImageDraw
import requests
import base64
import io
from function_utility import get_section_indices
from sectioning import split_image_with_gaps, outline_sections_on_image
from config import OPENAI_API_KEY



def encode_image_from_pil(pil_image):
  buffered = io.BytesIO()
  pil_image.save(buffered, format="PNG")
  return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Your OpenAI API key

# Function to call the OpenAI API with the encoded image
messages =  [
]
def append_message(is_user, text, image=None):
    """
    Appends a user or assistant message to the existing messages list.

    :param is_user: Boolean indicating if the message is from a user (True) or an assistant (False).
    :param text: The text content of the message.
    :param messages: List of existing messages.
    :param image: Optional PIL image for user messages.
    """

    # Construct the basic message structure
    message = {
        "role": "user" if is_user else "system",
        "content": [{"type": "text", "text": text}]
    }

    # For user messages, encode and add the image if provided
    if is_user and image is not None:
        base64_image = encode_image_from_pil(image)
        message["content"].append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
        })

    # Append the message to the messages list
    messages.append(message)

def call_openai_api_with_image():
  headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {OPENAI_API_KEY}"
  }

  payload = {
      "model": "gpt-4-vision-preview",
      "messages": messages,
      "max_tokens": 300
  }

  response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
  print(response.json())
  return response.json()['choices'][0]['message']['content']


def main():
    original_image_path = 'images/ispy.png'
    original_image = Image.open(original_image_path)
    sections_dict, split_image = split_image_with_gaps(original_image, None, 'images/ss1.png', save=True)
    append_message(True, f"I spy with my little eye something that is spooky", split_image)
    api_response = call_openai_api_with_image()
    append_message(False, api_response)
    print(api_response)
    indices = get_section_indices(api_response)
    print(indices)
    sections_dict, split_image = split_image_with_gaps(sections_dict, indices, 'images/ss2.png', save=True)
    append_message(True, f"In what sections is the object?", split_image)
    api_response = call_openai_api_with_image()
    append_message(False, api_response)
    print(api_response)
    indices = get_section_indices(api_response)
    print(indices)
    outline_sections_on_image(original_image, sections_dict, indices, save=True, save_path=f'images/ss3.png')

if __name__ == "__main__":
    main()
