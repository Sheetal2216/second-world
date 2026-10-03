import { useEffect, useState } from "react";

function App() {
  const [message, setMessage] = useState("Connecting to backend...");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/")
      .then((response) => response.json())
      .then((data) => {
        setMessage(data.message);
      })
      .catch(() => {
        setMessage("Could not connect to backend");
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <h1 className="text-4xl font-bold text-white">
        {message}
      </h1>
    </div>
  );
}

export default App;