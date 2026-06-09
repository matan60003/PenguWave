import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const location = useLocation();
  const { user, logout } = useAuth();

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/events" style={{ textDecoration: "none", color: "inherit" }}>
          PenguWave 🐧
        </Link>
      </div>
      <div className="navbar-links">
        <Link
          to="/events"
          className={location.pathname.startsWith("/events") ? "active" : ""}
        >
          Events
        </Link>
        {user?.role === "admin" && (
          <Link
            to="/users"
            className={location.pathname === "/users" ? "active" : ""}
          >
            Users
          </Link>
        )}
        {user ? (
          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <span style={{ fontSize: "14px", color: "#666" }}>
              {user.email} <strong style={{color:"#333"}}>({user.role})</strong>
            </span>
            <button onClick={logout} className="navbar-login-btn" style={{ background: "#ccc", color: "#333" }}>
              Logout
            </button>
          </div>
        ) : (
          <Link to="/login">
            <button className="navbar-login-btn">Login</button>
          </Link>
        )}
      </div>
    </nav>
  );
}
