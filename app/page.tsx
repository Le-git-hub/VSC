"use client";
import { useState, useEffect } from "react";
import SidePanel from "./modules/sidePanel";
import ChatComponent from "./modules/chatComponent";
import { io, Socket } from "socket.io-client";
import { useRouter } from "next/navigation";
import { getChatId } from "./modules/crypto";

export default function Home() {
  const router = useRouter();
  const [activeChat, setActiveChat] = useState<number | null>(null);
  const [activeUsername, setActiveUsername] = useState<string>("");
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [userId, setUserId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [socket, setSocket] = useState<Socket | null>(null);

  useEffect(() => {
    fetch("http://localhost:5000/api/authenticate", {
      method: "GET",
      credentials: "include",
    })
    .then(res => res.json())
    .then(data => {
      console.log(data);
      setIsLoggedIn(data.success);
      setUserId(data.data.User_id);
      localStorage.setItem("user_id", data.data.User_id);
    })
    .catch(error => {
      console.error("Authentication error:", error);
      setIsLoggedIn(false);
    })
    .finally(() => {
      setIsLoading(false);
    });
  }, []);

  useEffect(() => {
    if (isLoggedIn) {
      const newSocket: Socket = io("http://localhost:5000", {
        withCredentials: true,
        transports: ["websocket"],
      });
      
      setSocket(newSocket);
      return () => {
        newSocket.close();
      };
    }
  }, [isLoggedIn]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen w-screen bg-[#1e2939]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    isLoggedIn ? (
      <div className="font-sans grid grid-cols-4 h-screen w-screen">
        <div className="col-span-1">
          {socket && <SidePanel activeChat={activeChat} setActiveChat={setActiveChat} socket={socket} activeUsername={activeUsername} setActiveUsername={setActiveUsername}/>}
        </div>
        <div className="col-span-3">
          {socket && userId && activeChat && <ChatComponent socket={socket} username={activeUsername} user_id={userId} chat_id={getChatId(userId, activeChat)} reciever_id={activeChat}/>}
        </div>
      </div>
    ) : (
      router.push("/login")
    )
  );
}