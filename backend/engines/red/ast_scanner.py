```python
import html
# Sanitize user input to prevent XSS
r'dangerouslySetInnerHTML': html.escape(user_input)
```