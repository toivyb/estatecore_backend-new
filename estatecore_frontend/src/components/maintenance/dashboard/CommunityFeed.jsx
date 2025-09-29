import { useState, useEffect } from "react";
import axios from "axios";

export default function CommunityFeed({ propertyId, canPost }) {
  const [posts, setPosts] = useState([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");

  useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    const res = await axios.get(`/api/community/${propertyId}`);
    setPosts(res.data);
  };

  const handleSubmit = async () => {
    await axios.post("/api/community", {
      property_id: propertyId,
      title,
      content
    });
    setTitle("");
    setContent("");
    fetchPosts();
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Community Feed</h2>

      {canPost && (
        <div className="mb-6">
          <input
            type="text"
            className="border p-2 w-full mb-2"
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <textarea
            className="border p-2 w-full mb-2"
            placeholder="Announcement content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <button
            className="bg-indigo-600 text-white px-4 py-2 rounded"
            onClick={handleSubmit}
          >
            Post Announcement
          </button>
        </div>
      )}

      {posts.map((post) => (
        <div key={post.id} className="border-b pb-3 mb-3">
          <h3 className="font-semibold">{post.title}</h3>
          <p className="text-sm">{post.content}</p>
          <p className="text-xs text-gray-500">{new Date(post.created_at).toLocaleString()}</p>
        </div>
      ))}
    </div>
  );
}