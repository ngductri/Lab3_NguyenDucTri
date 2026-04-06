# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Đức Trí
- **Student ID**: 2A202600394
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

During the development of the calendar booking agent, I contributed to the implementation of the agent.py module located in src/agent/. My work focused on enhancing the agent's decision-making capabilities by integrating a new tool for handling calendar conflicts.

Modules Implemented: src/agent/agent.py
Code Highlights: Added the resolve_conflicts() function to streamline conflict resolution. [See lines 45-78 in agent.py]
Documentation: The resolve_conflicts() function interacts with the ReAct loop by providing a structured response when overlapping events are detected, ensuring seamless integration with the agent's reasoning process.


---

## II. Debugging Case Study (10 Points)

During the lab, I encountered a failure event where the agent was unable to book a calendar event due to an error in the Google Calendar API call.

Problem Description: The agent attempted to execute the book_calendar_event tool but encountered the error: 'str' object has no attribute 'valid'.
Log Source: [Logs from 2026-04-06.log]:
`{"timestamp": "2026-04-06T08:48:15.367400", "level": "INFO", "service": "AI-Lab-Agent", "message": "TOOL_EXECUTED", "data": {"tool": "book_calendar_event", "args": "Title: Meeting with, YYYY-MM-DDTHH:MM:SS+07:00 | YYYY-MM-DDTHH:MM:SS+07:00 | Location", "observation": "Lỗi khi gọi Google Calendar API: 'str' object has no attribute 'valid'"}}`
Diagnosis: The issue occurred because the tool's arguments were not properly validated before being passed to the Google Calendar API. Specifically, the valid attribute was expected on an object, but a string was provided instead.
Solution: I resolved the issue by adding a validation step in the book_calendar_event function to ensure that all arguments passed to the API were properly formatted and of the correct type. This included checking for required attributes and converting strings to the appropriate objects where necessary.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

Reasoning: The Thought block significantly enhanced the agent's reasoning capability by allowing it to explicitly outline its intermediate steps before taking action. This structured reasoning process ensured that the agent could break down complex tasks into manageable steps, leading to more accurate and context-aware responses compared to a direct Chatbot answer, which often relies on a single-turn response without deeper reasoning.

Reliability: The agent performed worse than the Chatbot in scenarios where the task required minimal reasoning but high-speed responses, such as answering straightforward factual questions. In these cases, the additional reasoning steps introduced unnecessary latency, making the Chatbot more efficient.

Observation: The environment feedback (observations) played a crucial role in guiding the agent's next steps. For example, when a tool execution failed or returned unexpected results, the agent adjusted its reasoning and attempted alternative approaches. This iterative process allowed the agent to recover from errors and refine its actions based on real-time feedback.

---

## IV. Future Improvements (5 Points)

Scalability: To scale this system for production, I would implement an asynchronous task queue (e.g., using Celery or RabbitMQ) to handle tool calls. This would allow the agent to process multiple requests concurrently, improving throughput and responsiveness in high-demand scenarios.

Safety: Introducing a 'Supervisor' LLM to audit the agent's actions would enhance safety. The Supervisor could validate the agent's reasoning and outputs before execution, ensuring compliance with predefined constraints and reducing the risk of harmful or erroneous actions.

Performance: For a system with many tools, I would integrate a vector database (e.g., Pinecone or FAISS) for efficient tool retrieval. This would enable the agent to quickly identify the most relevant tools based on the context, reducing latency and improving overall performance.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.