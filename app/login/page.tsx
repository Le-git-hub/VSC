"use client";
import { RiAccountCircleFill } from "react-icons/ri";
import { VscEyeClosed, VscEye } from "react-icons/vsc";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Cookies from "js-cookie";
import Link from "next/link";

export default function Login() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [eyeClick, setEyeClick] = useState(false);
  const [loginResult, setLoginResult] = useState<null | boolean>(null);
  const [errorSuccessMessage, setErrorSuccessMessage] = useState("");
  useEffect(() => {
    if (Cookies.get("session_id")) {
      router.push("/");
      setLoginResult(true);
      setErrorSuccessMessage("You are already logged in");
    }
  }, []);
  const handleClick = async (username: string, password: string) => {
    if (username.length < 1 || password.length < 1) {
        setLoginResult(false);
        setErrorSuccessMessage("Please enter both username and password");
        return;
    } 
    try {
      const res = await fetch("http://localhost:5000/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const res_json = await res.json();

      if (res_json.success === true) {
        Cookies.set("session_id", res_json.session_id, { expires: 30 }); // Unsafe, can be exploited with XSS but its only for development
        
        router.push("/")
        setLoginResult(true)
        setErrorSuccessMessage("Login Successful")
      } else {
        setLoginResult(false);
        setErrorSuccessMessage("Login failed, "+res_json.message);
      }
    } catch (error) {
      setErrorSuccessMessage("Error Occurred, "+error);
      setLoginResult(false);
    }
  };

  return <div className="text-2xl font-bold flex items-center justify-center h-screen w-screen bg-linear-to-r from-cyan-200 to-blue-800 drop-shadow-2xl">
    <div className="bg-[#252627] w-xl h-[600px] rounded-2xl flex flex-col items-center">
        <RiAccountCircleFill className="mt-5" size={64}/>
        <h1 className="text-gray-200 text-3xl font-bold mt-5">Login</h1>
        <h2 className="text-gray-200 text-lg font-light mt-4 text-center w-[80%]">Sign in to your account with username and password</h2>
        <div className="flex flex-col items-center justify-center mt-[15%] space-y-2 w-[90%]">
            <input type="text" placeholder="Username" maxLength={16} className="w-full h-15 rounded-md border-2 border-gray-300 p-2" value={username} 
              onChange={(e) => setUsername(e.target.value)}/>
            <div className="relative w-full">
              <input type={eyeClick? "password" : "text"} placeholder="Password" maxLength={32} className="w-full h-15 rounded-md border-2 border-gray-300 p-2" value={password}
                onChange={(e) => setPassword(e.target.value)}  />
                {eyeClick ? 
                  <VscEye size={24} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 cursor-pointer" onClick={() => setEyeClick(!eyeClick)}/> 
                  : <VscEyeClosed size={24} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 cursor-pointer" onClick={() => setEyeClick(!eyeClick)}/>
                }
            </div>
            <button className="w-full h-15 rounded-md bg-blue-400 text-gray-700 shadow-lg hover:bg-blue-500 transition-all duration-200" onClick={() => handleClick(username, password)}>Login</button>
            {loginResult === true ? (
              <h2 className="text-green-400 font-light text-lg mt-2">{errorSuccessMessage}</h2>
            ): <h2 className="text-red-600 font-light text-lg mt-2">
              {errorSuccessMessage}
            </h2>}
            <h2 className="text-gray-200 font-light text-lg mt-2">
              Don't have an account? <Link href="/signup" className="text-blue-400 cursor-pointer">Signup</Link>
            </h2>
        </div>
    </div>

    
  </div>;
}