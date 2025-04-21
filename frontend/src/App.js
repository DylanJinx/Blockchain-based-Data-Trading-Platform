import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Web3Provider } from "./utils/web3";
import Navbar from "./components/Navbar";
import UploadPage from "./components/UploadPage";
import ChatPage from "./components/ChatPage";
import MarketPage from "./components/MarketPage";
import "./App.css";

function App() {
  return (
    <Web3Provider>
      <Router>
        <div className="App">
          <Navbar />
          <div className="container">
            <Routes>
              <Route path="/" element={<MarketPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/chat" element={<ChatPage />} />
            </Routes>
          </div>
        </div>
      </Router>
    </Web3Provider>
  );
}

export default App;
