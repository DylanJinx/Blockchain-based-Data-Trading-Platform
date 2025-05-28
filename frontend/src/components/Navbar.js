import React, { useState, useRef, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { useWeb3 } from "../utils/web3";
import styled from "styled-components";

const NavbarContainer = styled.nav`
  background-color: #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 1rem 2rem;
`;

const NavbarContent = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Logo = styled.div`
  font-size: 1.5rem;
  font-weight: bold;
  color: #4f46e5;
`;

const NavLinks = styled.div`
  display: flex;
  gap: 2rem;
`;

const NavLink = styled(Link)`
  text-decoration: none;
  color: ${(props) => (props.active ? "#4f46e5" : "#6b7280")};
  font-weight: ${(props) => (props.active ? "bold" : "normal")};

  &:hover {
    color: #4f46e5;
  }
`;

const WalletButton = styled.button`
  background-color: ${(props) => (props.connected ? "#10b981" : "#4f46e5")};
  color: white;
  border: none;
  border-radius: 5px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: background-color 0.3s ease;
  position: relative;

  &:hover {
    background-color: ${(props) => (props.connected ? "#059669" : "#4338ca")};
  }
`;

const WalletDropdown = styled.div`
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  background-color: white;
  border-radius: 5px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 200px;
  z-index: 10;
  display: ${(props) => (props.show ? "block" : "none")};
`;

const DropdownItem = styled.div`
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: #f3f4f6;
  }

  &:first-child {
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
  }

  &:last-child {
    border-bottom-left-radius: 5px;
    border-bottom-right-radius: 5px;
  }
`;

const NetworkBadge = styled.div`
  background-color: #f3f4f6;
  color: #4b5563;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  margin-left: 0.5rem;
  display: inline-block;
`;

const AccountInfo = styled.div`
  display: flex;
  flex-direction: column;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
`;

const AccountAddress = styled.div`
  font-size: 0.875rem;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 0.25rem;
  word-break: break-all;
`;

const NetworkInfo = styled.div`
  font-size: 0.75rem;
  color: #6b7280;
`;

const Navbar = () => {
  const {
    isConnected,
    account,
    connectWallet,
    disconnectWallet,
    switchAccount,
    networkName,
  } = useWeb3();
  const location = useLocation();
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  const shortenAddress = (address) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  // 点击外部关闭下拉菜单
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleWalletClick = async () => {
    if (isConnected) {
      setShowDropdown(!showDropdown);
    } else {
      await connectWallet();
    }
  };

  return (
    <NavbarContainer>
      <NavbarContent>
        <Logo>数据交易平台</Logo>
        <NavLinks>
          <NavLink to="/" active={location.pathname === "/" ? 1 : 0}>
            市场
          </NavLink>
          <NavLink
            to="/upload"
            active={location.pathname === "/upload" ? 1 : 0}
          >
            上传数据
          </NavLink>
          <NavLink
            to="/proof-packages"
            active={location.pathname === "/proof-packages" ? 1 : 0}
          >
            证明包下载
          </NavLink>
          <NavLink to="/chat" active={location.pathname === "/chat" ? 1 : 0}>
            客服小x
          </NavLink>
        </NavLinks>
        <div style={{ position: "relative" }} ref={dropdownRef}>
          <WalletButton
            connected={isConnected ? 1 : 0}
            onClick={handleWalletClick}
          >
            {isConnected ? shortenAddress(account) : "连接钱包"}
          </WalletButton>

          <WalletDropdown show={showDropdown ? 1 : 0}>
            {isConnected && (
              <>
                <AccountInfo>
                  <AccountAddress>{account}</AccountAddress>
                  <NetworkInfo>当前网络: {networkName}</NetworkInfo>
                </AccountInfo>
                <DropdownItem onClick={switchAccount}>切换账户</DropdownItem>
                <DropdownItem
                  onClick={() => {
                    disconnectWallet();
                    setShowDropdown(false);
                  }}
                >
                  断开连接
                </DropdownItem>
              </>
            )}
          </WalletDropdown>
        </div>
      </NavbarContent>
    </NavbarContainer>
  );
};

export default Navbar;
