# ALL CODEX IS IN PLan 

# Task 1 Part A: 

Asked AI To implement my prompt: 

Help me implement this task

Task 1: Core Chat Application (100 points)
Goal: Build the foundational ChatGPT-style app in four progressive stages. Complete each part before moving to the next — each part extends the previous one.

The diagram below shows the expected layout your app should match. Your implementation does not need to be pixel-perfect, but all elements must appear in the correct locations.

Screenshot 2026-03-13 at 12.07.20 PM-1.png

Part A: Page Setup & API Connection (20 points)
Requirements:

Use st.set_page_config(page_title="My AI Chat", layout="wide").
Load your Hugging Face token using st.secrets["HF_TOKEN"]. The token must never be hardcoded in app.py.
If the token is missing or empty, display a clear error message in the app. The app must not crash.
Send a single hardcoded test message (e.g. "Hello!") to the Hugging Face API using the loaded token and display the model’s response in the main area.
Handle API errors gracefully (missing token, invalid token, rate limit, network failure) with a user-visible message rather than a crash.
Success criteria (Part A): Running streamlit run app.py with a valid .streamlit/secrets.toml sends a test message and displays the model’s reply. Running it without the secrets file shows an error message instead of crashing.

AI suggestions: 
- How should the Part A plan handle the required hardcoded test message?
1. Auto-send on load (Recommended)
2. Button-triggered test
3. Keep editable prompt

My Response: I asked ai to use the recommended option and tested it to work. 
Token didn't work at first but it was just because i didn't save it with my replaced real token

# Part B: 

Asked AI to implement my prompt: 

Help me implement this

Part B: Multi-Turn Conversation UI (30 points)
Requirements:

Extend Part A to replace the hardcoded test message with a real input interface.
Use native Streamlit chat UI elements. Render messages with st.chat_message(...) and collect user input with st.chat_input(...).
Add a fixed input bar at the bottom of the main area.
Store the full conversation history in st.session_state. After each exchange, append both the user message and the assistant response to the history.
Send the full message history with each API request so the model maintains context.
Render the conversation history above the input bar using default Streamlit UI elements rather than CSS-based custom chat bubbles.
The message history must scroll independently of the input bar — the input bar stays visible at all times.
Success criteria (Part B): Sending multiple messages in a row produces context-aware replies (e.g. the model remembers the user’s name from an earlier message). Messages are displayed with correct styling and the input bar remains fixed.

AI Suggestions: How should the Part B plan initialize the conversation history?
1. Start empty (Recommended)
2. Starter assistant message

My Response: I asked ai to go with the recommened plan and tested everything to work
It all works I typed and it responded 

# Part C: 

Asked AI to implement my prompt: 

Help me implement this

Part C: Chat Management (25 points)
Requirements:

Add a New Chat button to the sidebar that creates a fresh, empty conversation and adds it to the sidebar chat list.
Use the native Streamlit sidebar (st.sidebar) for chat navigation.
The sidebar shows a scrollable list of all current chats, each displaying a title and timestamp.
The currently active chat must be visually highlighted in the sidebar.
Clicking a chat in the sidebar switches to it without deleting or overwriting any other chats.
Each chat entry must have a ✕ delete button. Clicking it removes the chat from the list. If the deleted chat was active, the app must switch to another chat or show an empty state.
Success criteria (Part C): Multiple chats can be created, switched between, and deleted independently. The active chat is always visually distinct.

AI Suggstions: 
- How should the Part C plan handle chat storage?
1. Session only (Recommended)
2. Persist to chats/ now

My Response: Asked AI to go with recommened and then I went on to test if it all worked
Everything worked

# Part D: 

Asked Ai to implement my prompt: 

Help me implement this 

Part D: Chat Persistence (25 points)
Requirements:

Each chat session is saved as a separate JSON file inside a chats/ directory. Each file must store at minimum: a chat ID, a title or timestamp, and the full message history.
On app startup, all existing files in chats/ are loaded and shown in the sidebar automatically.
Returning to a previous chat and continuing the conversation must work correctly.
Deleting a chat (✕ button) must also delete the corresponding JSON file from chats/.
A generated or summarized chat title is acceptable and encouraged. The title does not need to be identical to the first user message.
Success criteria (Part D): Closing and reopening the app shows all previous chats intact in the sidebar. Continuing a loaded chat works correctly. Deleting a chat removes its file from disk.

Ai suggestions: 
- How should the Part D plan name each chat JSON file in `chats/`?
1.Use chat ID (Recommended)
2.Use timestamp
3.Use title slug

My response: Asked ai to implement the recommened and tested to see if it works 
Everything works well and no porblems

# Task 2 

Asked Ai to help me implement my prompt: 

Help me implement this 

Task 2: Response Streaming (20 points)
Goal: Display the model’s reply token-by-token as it is generated instead of waiting for the full response.

Requirements
Use the stream=True parameter in your API request and handle the server-sent event stream.
In Streamlit, use native Streamlit methods such as st.write_stream() or manually update a placeholder with st.empty() as chunks arrive.
The full streamed response must be saved to the chat history once streaming is complete.
Hint: Add stream=True to your request payload and set stream=True on the requests.post() call. The response body will be a series of data: lines in SSE format.

Note: Very small models such as meta-llama/Llama-3.2-1B-Instruct may stream so quickly that the output appears to arrive all at once. If your app is correctly receiving multiple streamed chunks but the effect is too fast to notice, you are required to add a very short delay between rendering chunks so the streaming behavior is visible in the UI.

Success criteria: Responses appear incrementally in the chat interface and are correctly saved to history.

AI Suggestion: How should the streaming plan render the assistant response in Streamlit?
1.Use st.write_stream (Recommended)
2.Use st.empty manually

My response: Used the recommened one and then went to test out everything 
test went well and it was token-by-token as wanted

# Task 3: 

Asked AI to help me implement my prompt: 

Help me implement this 

Task 3: User Memory (20 points)
Goal: Extract and store user preferences from conversations, then use them to personalize future responses.

Requirements
After each assistant response, make a second lightweight API call asking the model to extract any personal traits or preferences mentioned by the user in that message.
Extracted traits are stored in a memory.json file. Example categories might include name, preferred language, interests, communication style, favorite topics, or other useful personal preferences.
The sidebar displays a User Memory expander panel showing the currently stored traits.
Include a native Streamlit control to clear/reset the saved memory.
Stored memory is injected into the system prompt of future conversations so the model can personalize responses.
Implementation note: The categories above are only examples for reference. It is up to you to decide what traits to store, how to structure your memory.json, how to merge or update existing memory, and how to incorporate that memory into future prompts, as long as the final app clearly demonstrates persistent user memory and personalization.

Hint: A simple memory extraction prompt might look like: “Given this user message, extract any personal facts or preferences as a JSON object. If none, return {}”

Success criteria: User traits are extracted, displayed in the sidebar, and used to personalize subsequent responses.

AI suggestions: How should the Task 3 plan structure stored user memory in `memory.json`?
1.Flat named traits (Recommended)
2.Free-form facts list
3.Nested profile

My response: Use the recommened and then went to test it
Everything works well

I couldn't get the github to work and I am running out of time so I will just include network url and local url instead

Local URL: http://localhost:8501
  Network URL: http://10.0.0.161:8501