// static/js/chat.js
const chatMessages = document.getElementById("chat-messages");
const messageInput = document.getElementById("user-message");
const chatForm = document.getElementById("chat-form");

// Load chat history on page load
fetch("/chat/messages")
  .then(res => res.json())
  .then(messages => {
    messages.forEach(msg => {
      const bubble = document.createElement("div");
      bubble.className = `mb-2 text-${msg.sender === 'user' ? 'end' : 'start'}`;
      bubble.innerHTML = `<span class='badge bg-${msg.sender === 'user' ? 'primary' : 'secondary'}'>${msg.content}</span>`;
      chatMessages.appendChild(bubble);
    });
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });

// Send message
chatForm.addEventListener("submit", function(event) {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;

  fetch("/chat/send", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ message })
  })
    .then(res => res.json())
    .then(data => {
      const bubble = document.createElement("div");
      bubble.className = "mb-2 text-end";
      bubble.innerHTML = `<span class='badge bg-primary'>${data.content}</span>`;
      chatMessages.appendChild(bubble);
      chatMessages.scrollTop = chatMessages.scrollHeight;
      messageInput.value = "";
    });
});
