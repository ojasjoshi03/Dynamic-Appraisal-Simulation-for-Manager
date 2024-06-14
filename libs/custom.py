from PIL import Image
import base64
from .set_context import set_context

# username
user_name = 'Manager'
gpt_name = 'Employee'
# Content Background
user_background_color = ''
gpt_background_color = 'rgba(225, 230, 235, 0.5)'
# Initial model settings
initial_content_all = {
    "history": [],
    "contexts": {
        'context_select': 'Not set',
        'context_input': '',
        'context_level': 3
    }
}
# Context
set_context_all = {"Not set": ""}
set_context_all.update(set_context)
