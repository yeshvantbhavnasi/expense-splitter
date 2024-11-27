import { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { useAuth } from '../contexts/AuthContext';
import { userService } from '../api/services';
import { User } from '../types';

export default function Profile() {
  const { user: authUser, updateUser } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [uploadingImage, setUploadingImage] = useState(false);

  useEffect(() => {
    if (authUser) {
      setFormData((prev) => ({
        ...prev,
        full_name: authUser.full_name,
        email: authUser.email,
      }));
    }
  }, [authUser]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedImage(e.target.files[0]);
    }
  };

  const handleImageUpload = async () => {
    if (!selectedImage) return;
    
    setUploadingImage(true);
    setError('');
    
    try {
      const { url } = await userService.uploadProfilePicture(selectedImage);
      // Update the user object with the new profile picture URL
      if (authUser) {
        updateUser({ ...authUser, profile_picture_url: url });
      }
      setSelectedImage(null);
    } catch (err) {
      setError('Failed to upload profile picture');
      console.error('Upload error:', err);
    } finally {
      setUploadingImage(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (formData.new_password) {
        if (formData.new_password !== formData.confirm_password) {
          throw new Error('New passwords do not match');
        }
        // Update password
        await userService.updatePassword(formData.current_password, formData.new_password);
      }

      // Update profile
      const updatedUser = await userService.updateProfile({
        full_name: formData.full_name,
        email: formData.email,
      });

      updateUser(updatedUser);
      setIsEditing(false);
      setFormData((prev) => ({
        ...prev,
        current_password: '',
        new_password: '',
        confirm_password: '',
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-2xl font-semibold text-gray-900 mb-8">Profile Settings</h1>

          {/* Profile Picture Section */}
          <div className="bg-white shadow sm:rounded-lg mb-8">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center space-x-6">
                <div className="flex-shrink-0">
                  <div className="h-24 w-24 rounded-full bg-gray-100 flex items-center justify-center overflow-hidden">
                    {authUser?.profile_picture_url ? (
                      <img
                        src={authUser.profile_picture_url}
                        alt={authUser.full_name}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <span className="text-4xl text-gray-500">
                        {authUser?.full_name.charAt(0)}
                      </span>
                    )}
                  </div>
                </div>
                <div>
                  <label
                    htmlFor="profile-picture"
                    className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 cursor-pointer"
                  >
                    Choose new picture
                    <input
                      type="file"
                      id="profile-picture"
                      accept="image/*"
                      className="sr-only"
                      onChange={handleImageChange}
                    />
                  </label>
                  {selectedImage && (
                    <button
                      type="button"
                      onClick={handleImageUpload}
                      disabled={uploadingImage}
                      className="ml-3 inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      {uploadingImage ? 'Uploading...' : 'Upload'}
                    </button>
                  )}
                  {selectedImage && (
                    <p className="mt-2 text-sm text-gray-500">
                      Selected: {selectedImage.name}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Profile Form */}
          <div className="md:grid md:grid-cols-3 md:gap-6">
            <div className="md:col-span-1">
              <div className="px-4 sm:px-0">
                <h3 className="text-lg font-medium leading-6 text-gray-900">Profile</h3>
                <p className="mt-1 text-sm text-gray-600">
                  Update your personal information and password
                </p>
              </div>
            </div>

            <div className="mt-5 md:mt-0 md:col-span-2">
              <form onSubmit={handleSubmit}>
                <div className="shadow sm:rounded-md sm:overflow-hidden">
                  <div className="px-4 py-5 bg-white space-y-6 sm:p-6">
                    {error && (
                      <div className="rounded-md bg-red-50 p-4">
                        <div className="text-sm text-red-700">{error}</div>
                      </div>
                    )}

                    <div>
                      <label
                        htmlFor="full_name"
                        className="block text-sm font-medium text-gray-700"
                      >
                        Full Name
                      </label>
                      <input
                        type="text"
                        name="full_name"
                        id="full_name"
                        required
                        disabled={!isEditing}
                        className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md disabled:bg-gray-100"
                        value={formData.full_name}
                        onChange={handleInputChange}
                      />
                    </div>

                    <div>
                      <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                        Email
                      </label>
                      <input
                        type="email"
                        name="email"
                        id="email"
                        required
                        disabled={!isEditing}
                        className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md disabled:bg-gray-100"
                        value={formData.email}
                        onChange={handleInputChange}
                      />
                    </div>

                    {isEditing && (
                      <>
                        <div className="space-y-6">
                          <div>
                            <label
                              htmlFor="current_password"
                              className="block text-sm font-medium text-gray-700"
                            >
                              Current Password
                            </label>
                            <input
                              type="password"
                              name="current_password"
                              id="current_password"
                              className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                              value={formData.current_password}
                              onChange={handleInputChange}
                            />
                          </div>

                          <div>
                            <label
                              htmlFor="new_password"
                              className="block text-sm font-medium text-gray-700"
                            >
                              New Password
                            </label>
                            <input
                              type="password"
                              name="new_password"
                              id="new_password"
                              className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                              value={formData.new_password}
                              onChange={handleInputChange}
                            />
                          </div>

                          <div>
                            <label
                              htmlFor="confirm_password"
                              className="block text-sm font-medium text-gray-700"
                            >
                              Confirm New Password
                            </label>
                            <input
                              type="password"
                              name="confirm_password"
                              id="confirm_password"
                              className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                              value={formData.confirm_password}
                              onChange={handleInputChange}
                            />
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                  <div className="px-4 py-3 bg-gray-50 text-right sm:px-6">
                    {!isEditing ? (
                      <button
                        type="button"
                        onClick={() => setIsEditing(true)}
                        className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        Edit Profile
                      </button>
                    ) : (
                      <div className="flex justify-end space-x-3">
                        <button
                          type="button"
                          onClick={() => {
                            setIsEditing(false);
                            setError('');
                            if (authUser) {
                              setFormData((prev) => ({
                                ...prev,
                                full_name: authUser.full_name,
                                email: authUser.email,
                                current_password: '',
                                new_password: '',
                                confirm_password: '',
                              }));
                            }
                          }}
                          className="inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={loading}
                          className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                        >
                          {loading ? 'Saving...' : 'Save Changes'}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
