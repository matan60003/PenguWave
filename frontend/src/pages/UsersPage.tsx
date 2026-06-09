import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { User } from "../types";
import { getUsers, createUser, deleteUser } from "../api";
import { useAuth } from "../context/AuthContext";
import { createUserSchema, CreateUserFormValues } from "../utils/validation";

export default function UsersPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateUserFormValues>({
    resolver: zodResolver(createUserSchema),
    defaultValues: { role: "analyst" }
  });

  useEffect(() => {
    if (user?.role !== "admin") return;
    getUsers()
      .then(data => setUsers(data))
      .catch(err => console.error("Failed to fetch users", err));
  }, [user]);

  if (user?.role !== "admin") {
    return (
      <div className="page-container">
        <h2 style={{ color: "red" }}>Access Denied</h2>
        <p>You must be an administrator to view this page.</p>
      </div>
    );
  }

  const onSubmit = async (data: CreateUserFormValues) => {
    setError("");

    try {
      const newUser = await createUser(data);
      setUsers([...users, newUser]);
      reset();
      setShowForm(false);
    } catch (err: unknown) {
      setError((err instanceof Error ? err.message : "Failed to create user"));
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteUser(id);
      setUsers(users.filter((u) => u.id !== id));
    } catch (err: unknown) {
      alert("Failed to delete user: " + (err instanceof Error ? err.message : "Unknown error"));
    }
  };

  return (
    <div className="page-container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h1>User Management</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "Add User"}
        </button>
      </div>

      {showForm && (
        <div style={{ border: "1px solid #ddd", padding: 16, marginBottom: 20, background: "#fafafa" }}>
          <h3 style={{ marginBottom: 12 }}>New User</h3>
          {error && <div style={{ color: "red", marginBottom: 16 }}>{error}</div>}
          <form onSubmit={handleSubmit(onSubmit)}>
            <div style={{ marginBottom: 8 }}>
              <label>Email</label>
              <input
                type="email"
                {...register("email")}
                placeholder="user@penguwave.io"
                style={{ borderColor: errors.email ? "red" : undefined }}
              />
              {errors.email && <div style={{ color: "red", fontSize: 12, marginTop: 4 }}>{errors.email.message}</div>}
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>Password</label>
              <input
                type="text"
                {...register("password")}
                placeholder="password"
                style={{ borderColor: errors.password ? "red" : undefined }}
              />
              {errors.password && <div style={{ color: "red", fontSize: 12, marginTop: 4 }}>{errors.password.message}</div>}
            </div>
            <div style={{ marginBottom: 12 }}>
              <label>Role</label>
              <select {...register("role")}>
                <option value="admin">Admin</option>
                <option value="analyst">Analyst</option>
              </select>
            </div>
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create User"}
            </button>
          </form>
        </div>
      )}

      <table>
        <thead>
          <tr>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.email}</td>
              <td>{user.role}</td>
              <td>
                <span style={{ color: user.status === "active" ? "green" : "#999" }}>
                  {user.status}
                </span>
              </td>
              <td>
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    handleDelete(user.id);
                  }}
                  style={{ color: "red" }}
                >
                  Delete
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {users.length === 0 && <p style={{ color: "#999" }}>No users.</p>}
    </div>
  );
}
