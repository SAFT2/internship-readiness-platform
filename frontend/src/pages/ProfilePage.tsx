import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api, getErrorMessage } from "../lib/api";
import { useToast } from "../lib/useToast";

export function ProfilePage() {
  const [targetRole, setTargetRole] = useState("ML Intern");
  const [roles, setRoles] = useState<string[]>([]);
  const [rolesLoading, setRolesLoading] = useState(false);
  const [profileLoading, setProfileLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [skills, setSkills] = useState("python,sql,git");
  const [projectsCount, setProjectsCount] = useState(1);
  const [candidateYears, setCandidateYears] = useState(0.5);
  const [experienceType, setExperienceType] = useState("research");
  const [message, setMessage] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [assessingProfile, setAssessingProfile] = useState(false);
  const navigate = useNavigate();
  const { pushToast } = useToast();

  useEffect(() => {
    async function load() {
      try {
        setProfileLoading(true);
        setLoadError("");
        setRolesLoading(true);
        const [profileRes, rolesRes] = await Promise.all([
          api.get("/profile/me"),
          api.get<{ roles: string[] }>("/assessments/roles"),
        ]);

        const p = profileRes.data;
        const fetchedRoles = Array.from(new Set((rolesRes.data.roles || []).filter(Boolean)));
        setRoles(fetchedRoles);

        const savedRole = p.target_role || "ML Intern";
        const resolvedRole = fetchedRoles.includes(savedRole) ? savedRole : (fetchedRoles[0] || savedRole);
        setTargetRole(resolvedRole);
        setSkills((p.skills || []).join(","));
        setProjectsCount(p.projects_count || 0);
        setCandidateYears(p.candidate_years || 0);
        setExperienceType(p.experience_type || "none");
      } catch (err: unknown) {
        const msg = getErrorMessage(err, "Unable to load profile");
        setLoadError(msg);
        setMessage("No profile yet. Fill and save.");
      } finally {
        setRolesLoading(false);
        setProfileLoading(false);
      }
    }

    void load();
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setMessage("");
    setSavingProfile(true);

    try {
      await api.patch("/profile/me", {
        target_role: targetRole,
        skills: skills
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        projects_count: Number(projectsCount),
        candidate_years: Number(candidateYears),
        experience_type: experienceType,
      });
      setMessage("Profile saved.");
      pushToast("Profile saved", "success");
    } catch (err: unknown) {
      const msg = getErrorMessage(err, "Save failed");
      setMessage(msg);
      pushToast(msg, "error");
    } finally {
      setSavingProfile(false);
    }
  }

  async function assessFromProfile() {
    setAssessingProfile(true);
    setMessage("");
    try {
      const res = await api.post("/assessments/from-profile", { role: targetRole });
      pushToast("Profile assessment created", "success");
      navigate(`/assessments/${res.data.id}`);
    } catch (err: unknown) {
      const msg = getErrorMessage(err, "Profile assessment failed");
      setMessage(msg);
      pushToast(msg, "error");
    } finally {
      setAssessingProfile(false);
    }
  }

  return (
    <section className="panel">
      <h2>Profile</h2>

      {profileLoading && <p className="muted-text">Loading profile...</p>}
      {loadError && <p className="error-text">{loadError}</p>}
      {!profileLoading && roles.length === 0 && <p className="muted-text">Role catalog unavailable. Try refreshing later.</p>}

      <form onSubmit={onSubmit} className="form-grid">
        <label>
          Target Role
          <select value={targetRole} onChange={(e) => setTargetRole(e.target.value)} required disabled={rolesLoading || roles.length === 0}>
            {roles.length === 0 && <option value="">No roles available</option>}
            {roles.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </label>

        <label>
          Skills (comma separated)
          <input value={skills} onChange={(e) => setSkills(e.target.value)} required />
        </label>

        <label>
          Projects Count
          <input type="number" min={0} value={projectsCount} onChange={(e) => setProjectsCount(Number(e.target.value))} />
        </label>

        <label>
          Years Experience
          <input type="number" min={0} step="0.1" value={candidateYears} onChange={(e) => setCandidateYears(Number(e.target.value))} />
        </label>

        <label>
          Experience Type
          <select value={experienceType} onChange={(e) => setExperienceType(e.target.value)}>
            <option value="none">None</option>
            <option value="research">Research</option>
            <option value="internship">Internship</option>
            <option value="part-time">Part-time</option>
            <option value="full-time">Full-time</option>
          </select>
        </label>

        <button className="btn btn-primary" type="submit" disabled={savingProfile || profileLoading}>
          {savingProfile ? "Saving..." : "Save Profile"}
        </button>
        <button
          className="btn btn-outline"
          type="button"
          onClick={assessFromProfile}
          disabled={assessingProfile || profileLoading || roles.length === 0}
        >
          {assessingProfile ? "Assessing..." : "Assess From Profile"}
        </button>
      </form>

      {message && <p className="status-text">{message}</p>}
    </section>
  );
}
