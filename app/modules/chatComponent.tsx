"use client";

import React, { useState, useEffect } from "react";
import { AiOutlineSend } from "react-icons/ai";
import { saveChatKey, getChatKey } from "./indexedDB";
import { io, Socket } from "socket.io-client";
import { encryptMessage, importKey, decryptMessage } from "./crypto";
interface ChatProps {
  username: string;
  user_id: number | null;
  chat_id: string;
  reciever_id: number;
  socket: Socket;
}
interface Time {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
}

interface Message {
  sender: number;
  content: string;
  timestamp: number;
}
function unixToTime(unix: number): Time {
  const date = new Date(unix * 1000);
  return {
    year: date.getFullYear(),
    month: date.getMonth() + 1,
    day: date.getDate(),
    hour: date.getHours(),
    minute: date.getMinutes(),
  };
}
interface EncryptedMessage {
  ciphertext: string;
  iv: string;
  timestamp: number;
  sender: number;
  receiver: number;
}
const MessageItem: React.FC<Message & { user_id: number | null }> = ({ timestamp, content, sender, user_id }) => {
  const TimeObject = unixToTime(timestamp);
  return (
    <div className={`flex ${sender == user_id ? 'justify-start' : 'justify-end'} w-full mb-3`}>
      <div
        className={`flex flex-col rounded-2xl text-lg p-3 max-w-[70%] ${
          sender == user_id
            ? "bg-blue-500 text-white"
            : "bg-gray-500 text-white"
        }`}
      >
        <div className="break-words mb-1">{content}</div>
        <div className="text-xs text-gray-400 self-end leading-tight">
          {TimeObject.hour}:{TimeObject.minute.toString().padStart(2, "0")} {TimeObject.day}/{TimeObject.month}/{TimeObject.year}
        </div>
      </div>
    </div>
  );
};
const ChatComponent: React.FC<ChatProps> = ({ username, user_id, reciever_id, chat_id, socket }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  
  const [cachedKey, setCachedKey] = useState<CryptoKey | null>(null);
  const [keyLoaded, setKeyLoaded] = useState(false);

  useEffect(() => {
    const loadKey = async () => {
      const shared_key = await getChatKey(chat_id);
      if (shared_key) {
        const imported_key = await importKey(shared_key, 'raw');
        setCachedKey(imported_key);
      }
      else {
        console.error("Key not found for chat_id, messages are lost: " + chat_id);
      }
      setKeyLoaded(true);
    };
    loadKey();
  }, [chat_id]);

  useEffect(() => {
    if (!keyLoaded) return;

    socket.emit("get_history", { chat_id: chat_id });
    
    const handleMessageHistory = async (messages: { messages: EncryptedMessage[] }) => {
      const decrypted_messages = await DecryptMessages(messages.messages);
      setMessages(decrypted_messages?.filter(msg => msg !== null) || []);
    };

    const handleNewMessage = async (message: EncryptedMessage) => {
      const decrypted_message = await DecryptMessage(message, cachedKey);
      setMessages(prev => decrypted_message ? [...prev, decrypted_message] : prev);
    };

    socket.on("message_history", handleMessageHistory);
    socket.on("new_message", handleNewMessage);

    return () => {
      socket.off("message_history", handleMessageHistory);
      socket.off("new_message", handleNewMessage);
    };
  }, [socket, chat_id, keyLoaded]);

  const DecryptMessage = async (message: EncryptedMessage, shared_key: CryptoKey | null) => {
    if (shared_key == null) {
      return null;
    }
    const decrypted_content = await decryptMessage(shared_key, message);
    return {
      content: decrypted_content,
      timestamp: message.timestamp,
      sender: message.sender,
    };
  }

  const DecryptMessages = async (messages: EncryptedMessage[]) => {
    if (!cachedKey) return [];
    const decrypted_messages = await Promise.all(messages.map(async (message) => {
      return await DecryptMessage(message, cachedKey);
    }));
    return decrypted_messages;
  }

  const SendMessage = async (content: string, chat_id: string) => {
    if (!cachedKey) {
      console.error("Key not loaded yet");
      return;
    }
    
    const encrypted_content = await encryptMessage(cachedKey, content);
    socket.emit("send_message", {
      chat_id: chat_id,
      sender: user_id,
      receiver: reciever_id,
      ciphertext: encrypted_content.ciphertext,
      iv: encrypted_content.iv,
    });
  }
  return (
    <div className="flex flex-col h-screen w-full bg-gray-800">
      <div className="bg-[#35373a] h-[50px] flex items-center px-4 flex-shrink-0 border-b border-gray-600">
        <h1 className="font-bold text-xl text-white">{username}</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.map((message, index) => (
          <MessageItem
            key={index}
            timestamp={message.timestamp}
            content={message.content}
            sender={message.sender}
            user_id={user_id}
          />
        ))}
      </div>
      <div className="bg-[#35373a] h-[50px] flex relative items-center bottom-0 flex-shrink-0 border-b border-gray-600 ">
        <input className="font-bold text-white text-sm placeholder:font-light w-full h-full pl-2 focus:outline-none" placeholder="Type here" type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => {if (e.key === 'Enter') {SendMessage(input, chat_id); setInput("")}}} />
        <AiOutlineSend size={24} className="absolute right-5 cursor-pointer" onClick={() => {SendMessage(input, chat_id); setInput("")}} />
      </div>
    </div>
  );
};

export default ChatComponent;