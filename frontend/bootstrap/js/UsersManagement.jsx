import React, { useState, useEffect } from 'react';
import './UsersManagement.css';

const API_BASE_URL = (typeof window !== 'undefined' && window.location.origin ? window.location.origin : '') + '/api/v1';

/**
 * UsersManagement - A React component for managing users in the STMS system
 */
function UsersManagement() {
  // State variables
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    role: 'user'
  });
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch users when component mounts
  useEffect(() => {
    fetchUsers();
  }, []);

  // Function to fetch users from API
  const fetchUsers = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = (typeof localStorage !== 'undefined') ? (localStorage.getItem('token') || localStorage.getItem('stms_token')) : null;
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const response = await fetch(`${API_BASE_URL}/auth/users`, {
        headers,
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message || 'Unknown API error');
      }

      setUsers(data.users || []);
    } catch (error) {
      console.error("Could not fetch users:", error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // In a real app, you would implement adding/editing users here
    // This is a mockup since we don't have those endpoints in our API yet
    
    if (isEditing) {
      // Mock updating a user (in a real app, this would call the API)
      alert(`Edit functionality would update user ${editingId} with: ${JSON.stringify(formData)}`);
    } else {
      // Mock adding a new user (in a real app, this would call the API)
      alert(`Add functionality would create new user with: ${JSON.stringify(formData)}`);
    }
    
    // Reset form
    resetForm();
    
    // Refresh users list (in a real app, this would reflect the changes)
    fetchUsers();
  };

  // Reset the form fields and editing state
  const resetForm = () => {
    setFormData({
      name: '',
      email: '',
      role: 'user'
    });
    setIsEditing(false);
    setEditingId(null);
  };

  // Start editing a user
  const handleEdit = (user) => {
    setFormData({
      name: user.name,
      email: user.email,
      role: user.role || 'user'
    });
    setIsEditing(true);
    setEditingId(user.id);
  };

  // Delete a user
  const handleDelete = async (userId) => {
    // In a real app, this would call the API to delete the user
    if (window.confirm('Are you sure you want to delete this user?')) {
      alert(`Delete functionality would remove user ${userId}`);
      
      // Refresh users list (in a real app, this would reflect the deletion)
      fetchUsers();
    }
  };

  // Filter users based on search term
  const filteredUsers = users.filter(user => 
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="users-management">
      <h2>User Management</h2>
      
      {/* Error message */}
      {error && (
        <div className="error-message">
          Error: {error}
          <button onClick={fetchUsers}>Try Again</button>
        </div>
      )}
      
      {/* User Form */}
      <div className="user-form-container">
        <h3>{isEditing ? 'Edit User' : 'Add New User'}</h3>
        <form onSubmit={handleSubmit} className="user-form">
          <div className="form-group">
            <label htmlFor="name">Name</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="role">Role</label>
            <select
              id="role"
              name="role"
              value={formData.role}
              onChange={handleInputChange}
            >
              <option value="user">User</option>
              <option value="admin">Admin</option>
              <option value="operator">Operator</option>
              <option value="analyst">Analyst</option>
            </select>
          </div>
          
          <div className="form-actions">
            <button type="submit" className="btn-primary">
              {isEditing ? 'Update User' : 'Add User'}
            </button>
            {isEditing && (
              <button type="button" onClick={resetForm} className="btn-secondary">
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>
      
      {/* Users List */}
      <div className="users-list-container">
        <div className="users-list-header">
          <h3>System Users</h3>
          <div className="search-container">
            <input
              type="text"
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
          <button onClick={fetchUsers} disabled={loading} className="refresh-btn">
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
        
        {/* Loading indicator */}
        {loading && <div className="loading">Loading users...</div>}
        
        {/* No users message */}
        {!loading && !error && filteredUsers.length === 0 && (
          <p className="no-users">No users found.</p>
        )}
        
        {/* Users table */}
        {!loading && !error && filteredUsers.length > 0 && (
          <table className="users-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((user) => (
                <tr key={user.id}>
                  <td>{user.id}</td>
                  <td>{user.name}</td>
                  <td>{user.email}</td>
                  <td className={`role ${user.role || 'user'}`}>
                    {user.role || 'user'}
                  </td>
                  <td className="actions">
                    <button
                      onClick={() => handleEdit(user)}
                      className="edit-btn"
                      title="Edit user"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(user.id)}
                      className="delete-btn"
                      title="Delete user"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default UsersManagement;