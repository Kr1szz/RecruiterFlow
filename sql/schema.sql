-- Recruiter Bot schema. Seeding rebuilds it from scratch, so drop everything first
-- (including tables from an earlier, denormalized version of this schema).
DROP TABLE IF EXISTS job_required_skills, job_culture_keywords,
    candidate_skills, job_skills, candidate_traits, job_culture,
    skills, traits, candidates, jobs CASCADE;

CREATE TABLE candidates (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    experience_years INTEGER NOT NULL CHECK (experience_years >= 0),
    availability TEXT NOT NULL
        CHECK (availability IN ('immediate', '2_weeks', 'not_looking')),
    quirk TEXT NOT NULL
);

CREATE TABLE jobs (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title TEXT NOT NULL UNIQUE,
    min_experience INTEGER NOT NULL CHECK (min_experience >= 0),
    tagline TEXT NOT NULL
);

CREATE TABLE skills (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- One vocabulary for both candidate traits and job culture keywords, so culture
-- fit is a plain join on trait_id.
CREATE TABLE traits (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE candidate_skills (
    candidate_id INTEGER NOT NULL
        REFERENCES candidates(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL
        REFERENCES skills(id) ON DELETE RESTRICT,
    PRIMARY KEY (candidate_id, skill_id)
);

CREATE TABLE job_skills (
    job_id INTEGER NOT NULL
        REFERENCES jobs(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL
        REFERENCES skills(id) ON DELETE RESTRICT,
    PRIMARY KEY (job_id, skill_id)
);

CREATE TABLE candidate_traits (
    candidate_id INTEGER NOT NULL
        REFERENCES candidates(id) ON DELETE CASCADE,
    trait_id INTEGER NOT NULL
        REFERENCES traits(id) ON DELETE RESTRICT,
    PRIMARY KEY (candidate_id, trait_id)
);

CREATE TABLE job_culture (
    job_id INTEGER NOT NULL
        REFERENCES jobs(id) ON DELETE CASCADE,
    trait_id INTEGER NOT NULL
        REFERENCES traits(id) ON DELETE RESTRICT,
    PRIMARY KEY (job_id, trait_id)
);

CREATE INDEX idx_candidate_skills_skill_id ON candidate_skills(skill_id);
CREATE INDEX idx_job_skills_skill_id ON job_skills(skill_id);
CREATE INDEX idx_candidate_traits_trait_id ON candidate_traits(trait_id);
CREATE INDEX idx_job_culture_trait_id ON job_culture(trait_id);
