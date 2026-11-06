import { useEffect, useState } from "react";
import "../userProfile.css";

const emptyProfile = {
  primary_role: "",
  target_roles: [],
  experience_level: "",
  education: [],
  skills: [],
  projects: [],
  experience: [],
  certifications: [],
};

const emptyUser = {
  username: "",
  email: "",
  first_name: "",
  last_name: "",
  profile_picture: "",
  profile_picture_url: "",
};

const UserProfile = () => {
  const [user, setUser] = useState(emptyUser);
  const [profile, setProfile] = useState(emptyProfile);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [showTargetRoles, setShowTargetRoles] = useState(false);
  const [profileImageFile, setProfileImageFile] = useState(null);

  const token = localStorage.getItem("accessToken");

  useEffect(() => {
    fetchProfile();
  }, []);

  /* =========================================
     FETCH PROFILE
  ========================================= */

  const fetchProfile = async () => {
    try {
      const response = await fetch("http://localhost:8000/accounts/profile/", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (response.ok) {
        const profileUser = {
          ...emptyUser,
          ...data.user,
          profile_picture: data.user?.profile_picture || "",
          profile_picture_url: data.user?.profile_picture_url || "",
        };

        setUser({
          ...profileUser,
        });
        localStorage.setItem("currentUser", JSON.stringify(profileUser));

        setProfile({
          ...emptyProfile,
          ...data.profile,
        });
      } else {
        setMessage(data.message || "Failed to load profile.");
      }
    } catch (error) {
      console.error(error);
      setMessage("Unable to connect to the server.");
    } finally {
      setLoading(false);
    }
  };

  /* =========================================
     USER FIELD CHANGE
  ========================================= */

  const handleUserChange = (e) => {
    const { name, value } = e.target;

    setUser((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  /* =========================================
     PROFILE PICTURE UPLOAD
  ========================================= */

  const handleImageChange = (e) => {
    const file = e.target.files?.[0];

    if (!file) {
      return;
    }

    setProfileImageFile(file);

    setUser((prev) => ({
      ...prev,
      profile_picture: file,
      profile_picture_url: "",
    }));
  };

  /* =========================================
     PROFILE FIELD CHANGE
  ========================================= */

  const handleChange = (e) => {
    const { name, value } = e.target;

    setProfile((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  /* =========================================
     ADD ITEM
  ========================================= */

  const addItem = (field) => {
    setProfile((prev) => ({
      ...prev,
      [field]: [...prev[field], ""],
    }));
  };

  /* =========================================
     UPDATE ITEM
  ========================================= */

  const updateItem = (field, index, value) => {
    setProfile((prev) => {
      const updated = [...prev[field]];

      updated[index] = value;

      return {
        ...prev,
        [field]: updated,
      };
    });
  };

  /* =========================================
     REMOVE ITEM
  ========================================= */

  const removeItem = (field, index) => {
    setProfile((prev) => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index),
    }));
  };

  /* =========================================
     PROFILE PICTURE PREVIEW
  ========================================= */

  const getProfilePicturePreview = () => {
    if (user.profile_picture instanceof File) {
      return URL.createObjectURL(user.profile_picture);
    }

    if (user.profile_picture) {
      return user.profile_picture;
    }

    if (user.profile_picture_url) {
      return user.profile_picture_url;
    }

    return null;
  };

  /* =========================================
     SUBMIT
  ========================================= */

  const handleSubmit = async (e) => {
    e.preventDefault();

    setSaving(true);
    setMessage("");

    try {
      const formData = new FormData();

      formData.append("username", user.username);
      formData.append("email", user.email);
      formData.append("first_name", user.first_name);
      formData.append("last_name", user.last_name);

      // Profile picture
      if (profileImageFile) {
        formData.append("profile_picture", profileImageFile);
      } else {
        formData.append("profile_picture_url", user.profile_picture_url || "");
      }

      formData.append("primary_role", profile.primary_role);
      formData.append("target_roles", JSON.stringify(profile.target_roles));
      formData.append("experience_level", profile.experience_level);
      formData.append("education", JSON.stringify(profile.education));
      formData.append("skills", JSON.stringify(profile.skills));
      formData.append("projects", JSON.stringify(profile.projects));
      formData.append("experience", JSON.stringify(profile.experience));
      formData.append("certifications", JSON.stringify(profile.certifications));

      const response = await fetch(
        "http://localhost:8000/accounts/profile/update/",
        {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Failed to update profile.");
      }

      setMessage("Profile updated successfully.");

      setProfileImageFile(null);
      setUser((prev) => ({
        ...prev,
        ...data.user,
      }));
      localStorage.setItem(
        "currentUser",
        JSON.stringify({
          ...JSON.parse(localStorage.getItem("currentUser") || "{}"),
          ...data.user,
        }),
      );
      setProfile((prev) => ({
        ...prev,
        ...data.profile,
      }));
    } catch (error) {
      setMessage(error.message);
    } finally {
      setSaving(false);
    }
  };

  /* =========================================
     LOADING
  ========================================= */

  if (loading) {
    return (
      <div className="profile-loading">
        <div className="profile-loader"></div>
        <p>Loading your profile...</p>
      </div>
    );
  }

  const profilePicturePreview = getProfilePicturePreview();

  return (
    <main className="profile-page">
      {/* =========================================
          HEADER
      ========================================= */}

      <section className="profile-hero">
        <div className="profile-hero-icon">
          <span>✦</span>
        </div>

        <div>
          <p className="profile-eyebrow">PERSONAL PROFILE</p>

          <h1>
            Build your <span>career profile.</span>
          </h1>

          <p className="profile-description">
            Keep your skills, experience and career goals updated. This
            information helps power your AI career guidance, interviews and
            recommendations.
          </p>
        </div>
      </section>

      {/* =========================================
          ENTIRE PROFILE FORM
      ========================================= */}

      <form onSubmit={handleSubmit} className="profile-form">
        {/* =========================================
            ACCOUNT INFORMATION
        ========================================= */}

        <ProfileCard
          number="01"
          title="Account Information"
          description="Manage your basic account information."
        >
          <div className="profile-account">
            {/* =====================================
                AVATAR
            ===================================== */}

            <div className="profile-avatar">
              {profilePicturePreview ? (
                <img src={profilePicturePreview} alt="Profile" />
              ) : (
                (user.first_name || user.username || user.email || "U")
                  .charAt(0)
                  .toUpperCase()
              )}
            </div>

            {/* =====================================
                USER FIELDS
            ===================================== */}

            <div className="profile-grid profile-account-fields">
              <ProfileField
                label="First Name"
                name="first_name"
                value={user.first_name}
                onChange={handleUserChange}
                placeholder="Enter your first name"
              />

              <ProfileField
                label="Last Name"
                name="last_name"
                value={user.last_name}
                onChange={handleUserChange}
                placeholder="Enter your last name"
              />

              <ProfileField
                label="Username"
                name="username"
                value={user.username}
                onChange={handleUserChange}
                placeholder="Enter your username"
              />

              <ProfileField
                label="Email"
                name="email"
                type="email"
                value={user.email}
                onChange={handleUserChange}
                placeholder="Enter your email"
              />

              {/* UPLOAD IMAGE */}

              <div className="profile-field profile-picture-field">
                <label>Profile Picture</label>

                <label className="image-upload">
                  <span className="upload-icon">+</span>

                  <span className="upload-text">
                    <strong>Choose a profile picture</strong>
                    <small>PNG, JPG or JPEG</small>
                  </span>

                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageChange}
                  />
                </label>
              </div>

              {/* =================================
                  IMAGE URL
              ================================= */}

              <ProfileField
                label="Profile Picture URL"
                name="profile_picture_url"
                value={user.profile_picture_url}
                onChange={handleUserChange}
                placeholder="https://example.com/profile.jpg"
              />
            </div>
          </div>
        </ProfileCard>

        {/* =========================================
            CAREER OVERVIEW
        ========================================= */}

        <ProfileCard
          number="02"
          title="Career Overview"
          description="Tell us where you are now and where you want to go."
        >
          <div className="profile-grid">
            {/* Primary Target Role */}

            <div className="profile-field">
              <label>Primary Target Role</label>

              <select
                name="primary_role"
                value={profile.primary_role}
                onChange={(e) => {
                  const role = e.target.value;

                  setProfile((prev) => ({
                    ...prev,

                    primary_role: role,

                    target_roles:
                      role && !prev.target_roles.includes(role)
                        ? [...prev.target_roles, role]
                        : prev.target_roles,
                  }));
                }}
              >
                <option value="">Select primary target role</option>

                <RoleOptions />
              </select>
            </div>

            {/* Target Roles */}

            <div className="profile-field">
              <div className="target-roles-header">
                <label>Target Roles</label>

                <button
                  type="button"
                  className="profile-add-button"
                  onClick={() => setShowTargetRoles((prev) => !prev)}
                >
                  <span>+</span>
                  Add
                </button>
              </div>

              {profile.target_roles.length > 0 && (
                <div className="selected-roles">
                  {profile.target_roles.map((role) => (
                    <span key={role} className="selected-role">
                      {role}

                      <button
                        type="button"
                        onClick={() =>
                          setProfile((prev) => ({
                            ...prev,

                            target_roles: prev.target_roles.filter(
                              (item) => item !== role,
                            ),
                          }))
                        }
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}

              {showTargetRoles && (
                <select
                  multiple
                  name="target_roles"
                  value={profile.target_roles}
                  onChange={(e) =>
                    setProfile((prev) => ({
                      ...prev,

                      target_roles: Array.from(
                        e.target.selectedOptions,
                        (option) => option.value,
                      ),
                    }))
                  }
                >
                  <RoleOptions />
                </select>
              )}
            </div>

            {/* Experience Level */}

            <div className="profile-field">
              <label>Experience Level</label>

              <select
                name="experience_level"
                value={profile.experience_level}
                onChange={handleChange}
              >
                <option value="">Select experience level</option>

                <option value="none">No Experience</option>

                <option value="intern">Intern</option>

                <option value="junior">Junior</option>

                <option value="mid_level">Mid-level</option>

                <option value="senior">Senior</option>
              </select>
            </div>
          </div>
        </ProfileCard>

        {/* =========================================
            EDUCATION
        ========================================= */}

        <ProfileCard
          number="03"
          title="Education"
          description="Add your academic background."
          action={<AddButton onClick={() => addItem("education")} />}
        >
          <RepeatableList
            field="education"
            items={profile.education}
            updateItem={updateItem}
            removeItem={removeItem}
            placeholder="B.E. Computer Engineering — XYZ University"
          />
        </ProfileCard>

        {/* =========================================
            SKILLS
        ========================================= */}

        <ProfileCard
          number="04"
          title="Skills"
          description="Add technologies and professional skills you know."
          action={<AddButton onClick={() => addItem("skills")} />}
        >
          <div className="skill-list">
            {profile.skills.length === 0 ? (
              <EmptyState text="No skills added yet." />
            ) : (
              profile.skills.map((skill, index) => (
                <div className="skill-item" key={index}>
                  <span className="skill-number">
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <input
                    value={
                      typeof skill === "string"
                        ? skill
                        : Object.values(skill || {}).join(" • ")
                    }
                    onChange={(e) =>
                      updateItem("skills", index, e.target.value)
                    }
                    placeholder="e.g. Python"
                  />

                  <RemoveButton onClick={() => removeItem("skills", index)} />
                </div>
              ))
            )}
          </div>
        </ProfileCard>

        {/* =========================================
            PROJECTS
        ========================================= */}

        <ProfileCard
          number="05"
          title="Projects"
          description="Showcase projects that demonstrate your abilities."
          action={<AddButton onClick={() => addItem("projects")} />}
        >
          <RepeatableList
            field="projects"
            items={profile.projects}
            updateItem={updateItem}
            removeItem={removeItem}
            placeholder="AI Interview & Examination System"
          />
        </ProfileCard>

        {/* =========================================
            EXPERIENCE
        ========================================= */}

        <ProfileCard
          number="06"
          title="Work Experience"
          description="Add internships, jobs or other professional experience."
          action={<AddButton onClick={() => addItem("experience")} />}
        >
          <RepeatableList
            field="experience"
            items={profile.experience}
            updateItem={updateItem}
            removeItem={removeItem}
            placeholder="Software Engineering Intern — ABC Technologies"
          />
        </ProfileCard>

        {/* =========================================
            CERTIFICATIONS
        ========================================= */}

        <ProfileCard
          number="07"
          title="Certifications"
          description="Add certificates and professional credentials."
          action={<AddButton onClick={() => addItem("certifications")} />}
        >
          <RepeatableList
            field="certifications"
            items={profile.certifications}
            updateItem={updateItem}
            removeItem={removeItem}
            placeholder="Python Programming Certification"
          />
        </ProfileCard>

        {/* =========================================
            SAVE
        ========================================= */}

        <div className="profile-save">
          <div className="profile-save-info">
            <span className="save-dot"></span>

            <div>
              <strong>Your profile is private</strong>

              <p>Your information is used to personalize your experience.</p>
            </div>
          </div>

          <button
            type="submit"
            className="profile-save-button"
            disabled={saving}
          >
            {saving ? (
              <>
                <span className="button-spinner"></span>
                Saving...
              </>
            ) : (
              <>
                Save Changes
                <span>→</span>
              </>
            )}
          </button>
        </div>

        {message && (
          <div
            className={`profile-message ${
              message.includes("successfully") ? "success" : "error"
            }`}
          >
            {message}
          </div>
        )}
      </form>
    </main>
  );
};

/* =========================================
   ROLE OPTIONS
========================================= */

const RoleOptions = () => {
  return (
    <>
      <option value="Network Engineer">Network Engineer</option>

      <option value="Engineering Manager">Engineering Manager</option>

      <option value="Penetration Tester / Ethical Hacker">
        Penetration Tester / Ethical Hacker
      </option>

      <option value="Scrum Master / Agile Coach">
        Scrum Master / Agile Coach
      </option>

      <option value="Solutions Architect">Solutions Architect</option>

      <option value="Platform Engineer">Platform Engineer</option>

      <option value="Database Administrator (DBA)">
        Database Administrator (DBA)
      </option>

      <option value="Blockchain / Smart Contract Developer">
        Blockchain / Smart Contract Developer
      </option>

      <option value="MLOps Engineer">MLOps Engineer</option>

      <option value="Computer Vision Engineer">Computer Vision Engineer</option>

      <option value="Game Developer">Game Developer</option>

      <option value="Data Scientist">Data Scientist</option>

      <option value="Sales / Solutions Engineer">
        Sales / Solutions Engineer
      </option>

      <option value="Technical Product Manager">
        Technical Product Manager
      </option>

      <option value="Security Operations (SOC) Analyst">
        Security Operations (SOC) Analyst
      </option>

      <option value="UX/UI Designer">UX/UI Designer</option>

      <option value="Business Intelligence (BI) Analyst">
        Business Intelligence (BI) Analyst
      </option>

      <option value="Data Engineer">Data Engineer</option>

      <option value="NLP Engineer">NLP Engineer</option>

      <option value="Test Automation Engineer">Test Automation Engineer</option>

      <option value="Cloud Infrastructure Engineer">
        Cloud Infrastructure Engineer
      </option>

      <option value="Fraud Analyst">Fraud Analyst</option>

      <option value="Site Reliability Engineer (SRE)">
        Site Reliability Engineer (SRE)
      </option>

      <option value="DevOps Engineer">DevOps Engineer</option>

      <option value="Mobile App Developer (iOS/Android)">
        Mobile App Developer (iOS/Android)
      </option>

      <option value="QA Engineer">QA Engineer</option>

      <option value="Robotics Engineer">Robotics Engineer</option>

      <option value="Frontend Developer">Frontend Developer</option>

      <option value="Full Stack Developer">Full Stack Developer</option>

      <option value="AI/ML Engineer">AI/ML Engineer</option>

      <option value="Backend Developer">Backend Developer</option>

      <option value="IoT Solutions Engineer">IoT Solutions Engineer</option>

      <option value="Application Security (AppSec) Engineer">
        Application Security (AppSec) Engineer
      </option>

      <option value="Data Analyst">Data Analyst</option>

      <option value="Embedded Systems Developer">
        Embedded Systems Developer
      </option>

      <option value="Systems Analyst">Systems Analyst</option>

      <option value="QA Automation Engineer">QA Automation Engineer</option>

      <option value="SDET (Software Development Engineer in Test)">
        SDET (Software Development Engineer in Test)
      </option>
    </>
  );
};

/* =========================================
   COMPONENTS
========================================= */

const ProfileCard = ({ number, title, description, action, children }) => {
  return (
    <section className="profile-card">
      <div className="profile-card-header">
        <div className="profile-card-title">
          <span className="profile-card-number">{number}</span>

          <div>
            <h2>{title}</h2>
            <p>{description}</p>
          </div>
        </div>

        {action}
      </div>

      <div className="profile-card-content">{children}</div>
    </section>
  );
};

/* =========================================
   PROFILE FIELD
========================================= */

const ProfileField = ({
  label,
  name,
  value,
  onChange,
  placeholder,
  type = "text",
}) => {
  return (
    <div className="profile-field">
      <label>{label}</label>

      <input
        type={type}
        name={name}
        value={value || ""}
        onChange={onChange}
        placeholder={placeholder}
      />
    </div>
  );
};

/* =========================================
   REPEATABLE LIST
========================================= */

const RepeatableList = ({
  field,
  items,
  updateItem,
  removeItem,
  placeholder,
}) => {
  if (items.length === 0) {
    return <EmptyState text="Nothing added yet. Click + Add to get started." />;
  }

  return (
    <div className="repeatable-list">
      {items.map((item, index) => {
        const displayValue =
          typeof item === "string"
            ? item
            : Object.values(item || {})
                .filter(Boolean)
                .join(" • ");

        return (
          <div className="repeatable-item" key={index}>
            <span className="repeatable-index">
              {String(index + 1).padStart(2, "0")}
            </span>

            <input
              type="text"
              value={displayValue}
              onChange={(e) => updateItem(field, index, e.target.value)}
              placeholder={placeholder}
            />

            <RemoveButton onClick={() => removeItem(field, index)} />
          </div>
        );
      })}
    </div>
  );
};

/* =========================================
   ADD BUTTON
========================================= */

const AddButton = ({ onClick }) => {
  return (
    <button type="button" className="profile-add-button" onClick={onClick}>
      <span>+</span>
      Add
    </button>
  );
};

/* =========================================
   REMOVE BUTTON
========================================= */

const RemoveButton = ({ onClick }) => {
  return (
    <button
      type="button"
      className="profile-remove-button"
      onClick={onClick}
      title="Remove"
    >
      ×
    </button>
  );
};

/* =========================================
   EMPTY STATE
========================================= */

const EmptyState = ({ text }) => {
  return (
    <div className="profile-empty">
      <span>＋</span>

      <p>{text}</p>
    </div>
  );
};

export default UserProfile;
