import os
import json
import random

def get_system_prompt():
  try:
      with open("current_prompt.json", "r") as f:
          current_prompt = json.load(f)
      behaviour = current_prompt.get("behaviour", "Humble")
      rating = current_prompt.get("rating", "High")
  except FileNotFoundError:
      behaviour = "Humble"
      rating = "High"

  # Path to the specific JSON file based on behavior and rating
  file_name = f"employee_type_data/{behaviour}_{rating}.json"
  
  try:
      with open(file_name, "r") as file:
          employee_data = json.load(file)
  except FileNotFoundError:
      performance_kpis = {
            "code_quality": "70%",
            "project_delivery": "On schedule",
            "team_collaboration": "Satisfactory",
            "innovation": "Minimal contributions"
          }
      employee_data = {
          "employee_id": "100",
          "name": "John Doe",
          "disposition": behaviour,
          "performance_rating": rating,
          "performance_kpis": performance_kpis,
          "manager_comments": "Shows remarkable dedication and insight."
      }
  
  try:
      with open("prompts/system_prompt1.txt", "r") as file:
          system_prompt = file.read().strip()
  except FileNotFoundError:
      system_prompt = f"You are a employee whose"

  learn_instruction = {
      "role": "system",
      "content": f"{system_prompt} Behaviour: {employee_data['disposition']}, Rating: {employee_data['performance_rating']}. Performance summary: {employee_data['performance_kpis']} Last manager comments: {employee_data['manager_comments']} Keep responses concise."
  }

  return learn_instruction

# Save messages for retrieval later on
def get_recent_messages():
  
  # Define the file name
  file_name = "stored_data.json"
  messages = []
  
  learn_instruction = get_system_prompt()

  # Append instruction to message
  messages.append(learn_instruction)

  # Get last messages
  try:
    with open(file_name) as user_file:
      data = json.load(user_file)
      
      # Append last 5 rows of data
      if data:
        if len(data) < 5:
          for item in data:
            messages.append(item)
        else:
          for item in data[-5:]:
            messages.append(item)
  except:
    pass

  
  # Return messages
  return messages

# Save messages for retrieval later on
def store_messages(request_message, response_message):

  # Define the file name
  file_name = "stored_data.json"

  # Get recent messages
  messages = get_recent_messages()[1:]

  # Add messages to data
  user_message = {"role": "user", "content": request_message}
  assistant_message = {"role": "assistant", "content": response_message}
  messages.append(user_message)
  messages.append(assistant_message)

  # Save the updated file
  with open(file_name, "w") as f:
    json.dump(messages, f)
 

# Reset Messages and Prompt
def reset_messages():

  # Messages File
  file_name = "stored_data.json"

  # Write an empty file
  open(file_name, "w")

  # Prompt File reset
  file_prompt = "current_prompt.json"
  open(file_prompt, "w")