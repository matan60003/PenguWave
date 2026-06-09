import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";

import EventsPage from "./pages/EventsPage";
import UsersPage from "./pages/UsersPage";
import NotFound from "./pages/NotFound";
import LoginPage from "./pages/LoginPage";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";

function App() {
  return (
    <AuthProvider>
      <Navbar />
      <div className="container">

        <Routes>
          <Route path="/" element={<Navigate to="/events" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/events"
            element={
              <ProtectedRoute>
                <EventsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/users"
            element={
              <ProtectedRoute>
                <UsersPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </AuthProvider>
  );
}

export default App;
