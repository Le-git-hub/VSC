"use client";
import React, { useEffect } from 'react'
import { useState } from 'react';
import { Socket } from 'socket.io-client';
import { getChatId, generateIdentityKey, exportKey, deriveSharedSecret, importKey } from './crypto';
import { getChatPrivateKey, saveChatPrivateKey, saveChatKey, getChatKey } from './indexedDB';
import { MdAccountCircle } from "react-icons/md";

interface ChatItemProps {
  title: string;
  unreadMessages: number;
  isActive?: boolean;
  onClick?: () => void;
}

interface Chat {
  chat_id: string;
  sender_id: number;
  reciever_id: number;
  sender_username: string;
  reciever_username: string;
  unread_messages: number;
}
interface SidePanelProps {
    activeChat: number | null;
    setActiveChat: (id: number) => void;
    socket: Socket;
    activeUsername: string;
    setActiveUsername: (username: string) => void;
}
const ChatBox: React.FC<ChatItemProps> = ({title, unreadMessages = 0, isActive = false, onClick}) => {
    if (isActive == true) {
        unreadMessages = 0;
    }
    return (<div className={isActive? 'flex items-center text-2xl cursor-pointer bg-blue-400 hover:bg-blue-300 w-full h-[170px] pl-5' : 'flex items-center text-2xl cursor-pointer bg-[#35373a] hover:bg-[#5d5f63] w-full h-[170px] pl-5' } onClick={onClick}>
        <MdAccountCircle size={32} className='rounded-full object-cover mr-3 flex-shrink-0 bg-gray-200'/>
        <div className="flex-1 min-w-0">
            <h3 className="font-medium text-gray-200 truncate">{title}</h3>
            <p className="text-sm text-gray-500 font-light truncate">Chat with {title}</p>
        </div>
        {unreadMessages > 0 && isActive == false && <div className='flex justify-center items-center bg-blue-500 rounded-full h-7 w-7 mr-5 text-sm'>
            {unreadMessages}
        </div>}

    </div>)
}
export default function SidePanel({
    activeChat,
    setActiveChat,
    activeUsername,
    setActiveUsername,
    socket
}: SidePanelProps) {
    const [username, setUsername] = useState<string>("");
    const [chats, setChats] = useState<Chat[]>([]);
    useEffect(() => {
      socket.emit("connected_chats");
      
      const handleConnectedChats = (data: {chats: Chat[]}) => {
          setChats(data.chats);
      };
      
      const handleNewKeyExchangeRequest = async (data: any) => {      
          const existingChatKey = await getChatKey(data.chat_id);
          if (existingChatKey != null) {
              console.log("Chat key already exists for chat_id:", data.chat_id, "ignoring request");
              return;
          }
          
          const identityKeys = await generateIdentityKey();
          const private_key = identityKeys.privateKey;
          const chatKey = await deriveSharedSecret(private_key, await importKey(data.public_key, 'spki'));
          const exportedChatKey = await exportKey(chatKey, 'raw');
          await saveChatKey(data.chat_id, exportedChatKey);
          socket.emit("key_exchange_success", { chat_id: data.chat_id, public_key: await exportKey(identityKeys.publicKey, 'spki') });
      };
      
      const handleKeyExchangeSuccess = async (data: any) => {      
          const existingChatKey = await getChatKey(data.chat_id);
          if (existingChatKey != null) {
              console.log("Chat key already exists for chat_id:", data.chat_id, "ignoring success");
              return;
          }
          
          const chat_id = data.chat_id;
          const public_key = data.public_key;
          const private_key = await getChatPrivateKey(chat_id);
          if (private_key == null) {
              console.log("ERROR: No private key found for chat_id:", chat_id);
              return;
          }
          const chatKey = await deriveSharedSecret(await importKey(private_key, 'pkcs8'), await importKey(public_key, 'spki'));
          const exportedChatKey = await exportKey(chatKey, 'raw');
          await saveChatKey(chat_id, exportedChatKey);
      };
      
      socket.on("connected_chats", handleConnectedChats);
      socket.on("new_key_exchange_request", handleNewKeyExchangeRequest);
      socket.on("key_exchange_success", handleKeyExchangeSuccess);
      return () => {
          socket.off("connected_chats", handleConnectedChats);
          socket.off("new_key_exchange_request", handleNewKeyExchangeRequest);
          socket.off("key_exchange_success", handleKeyExchangeSuccess);
      };
  }, [socket]);
    async function addChat(username: string) {

      const response = await fetch("http://localhost:5000/api/username_to_id", {
          method: "POST",
          headers: {
              "Content-Type": "application/json",
          },
          body: JSON.stringify({ username: username }),
      });
      if (response.status === 200) {
        const data = await response.json();
        const chat_id = getChatId(Number(localStorage.getItem("user_id")), data.data.User_id);
        const chatKey = await getChatKey(chat_id);
        const chatPrivateKey = await getChatPrivateKey(chat_id);
        if (chatKey != null || chatPrivateKey != null) {
          return;
        }
        const identityKeys = await generateIdentityKey();
        await saveChatPrivateKey(chat_id, await exportKey(identityKeys.privateKey, 'pkcs8'));
        
        socket.emit("key_exchange_request", { 
            reciever_id: data.data.User_id, 
            chat_id: chat_id, 
            public_key: await exportKey(identityKeys.publicKey, 'spki') 
        });
    }
    }
    const handleChatClick = (id: number) => {
        setActiveChat(Number(id));
        setChats((prevChats) =>(
        prevChats.map((chat) =>(
            chat.sender_id === id ? { ...chat, unreadMessages: 0 } : chat
        ))
        )
    )};
    
  return (
    <div className='h-full w-full relative'>
        <div className="flex-1 overflow-y-auto">
          <div className="h-screen w-full border-r-1 bg-[#35373a] border-black">
            {chats.map((chat) => (
              chat.reciever_id == Number(localStorage.getItem("user_id")) ? (
                <ChatBox
                  key={chat.chat_id}
                  title={chat.sender_username}
                  unreadMessages={chat.unread_messages}
                  isActive={activeChat === chat.sender_id }
                  onClick={() => {handleChatClick(chat.sender_id); setActiveUsername(chat.sender_username)}}
                />
                                
              ) : (
                <ChatBox
                  key={chat.chat_id}
                  title={chat.reciever_username}
                  unreadMessages={chat.unread_messages}
                  isActive={activeChat === chat.reciever_id }
                  onClick={() => {handleChatClick(chat.reciever_id); setActiveUsername(chat.reciever_username)}}
                />
                
              )
              
            ))}
          </div>
        </div>
        <div className='absolute bottom-5 left-5 w-full grid grid-cols-5 items-center gap-2 z-20'>
          <input type="text" placeholder="Add a new chat" className="col-span-4 h-10 px-4 rounded-lg bg-transparent border-2 border-gray-300 text-white focus:outline-none" value={username} onChange={(e) => setUsername(e.target.value)} onKeyDown={(e) => {if (e.key === 'Enter') {addChat(username); setUsername("")}}}/>
          <button className="col-span-1 w-12 h-12 text-2xl rounded-full bg-blue-400 text-white shadow-lg hover:bg-blue-500 transition-all duration-200 cursor-pointer" onClick={() => {addChat(username); setUsername("")}}>+</button>
        </div>
    </div>
  )
}