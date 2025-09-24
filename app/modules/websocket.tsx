import { io, Socket } from "socket.io-client";

export const socket = io("http://localhost:5000", {
    withCredentials: true,
    transports: ["websocket"],
});

export const connectChat = (chat_id: string) => {
    socket.emit("connect_chat", {
        chat_id: chat_id,
    });
}