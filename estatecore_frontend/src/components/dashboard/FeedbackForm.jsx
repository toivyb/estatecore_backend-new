import { useState } from "react";
export default function FeedbackForm() {
  const [msg, setMsg] = useState("");
  const send = async () => {
    await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg })
    });
    alert("Sent");
    setMsg("");
  };
  return <>
    <textarea value={msg} onChange={(e) => setMsg(e.target.value)} />
    <button onClick={send}>Send Feedback</button>
  </>;
}