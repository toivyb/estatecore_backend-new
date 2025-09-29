import { useState } from "react";
export default function NotificationSender({ userId }) {
  const [msg, setMsg] = useState("");
  const send = async () => {
    await fetch("/api/notify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ to: userId, type: "info", message: msg })
    });
    setMsg(""); alert("Sent");
  };
  return <>
    <input value={msg} onChange={e => setMsg(e.target.value)} placeholder="Notification..." />
    <button onClick={send}>Send</button>
  </>;
}