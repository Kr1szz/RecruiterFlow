CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    experience_years INTEGER NOT NULL CHECK (experience_years >= 0),
    availability TEXT NOT NULL
        CHECK (availability IN ('immediate', '2_weeks', 'not_looking')),
    quirk TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL UNIQUE,
    min_experience INTEGER NOT NULL CHECK (min_experience >= 0),
    tagline TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS traits (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS candidate_skills (
    candidate_id INTEGER NOT NULL
        REFERENCES candidates(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL
        REFERENCES skills(id) ON DELETE RESTRICT,
    PRIMARY KEY (candidate_id, skill_id)
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id INTEGER NOT NULL
        REFERENCES jobs(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL
        REFERENCES skills(id) ON DELETE RESTRICT,
    PRIMARY KEY (job_id, skill_id)
);

CREATE TABLE IF NOT EXISTS candidate_traits (
    candidate_id INTEGER NOT NULL
        REFERENCES candidates(id) ON DELETE CASCADE,
    trait_id INTEGER NOT NULL
        REFERENCES traits(id) ON DELETE RESTRICT,
    PRIMARY KEY (candidate_id, trait_id)
);

CREATE TABLE IF NOT EXISTS job_culture (
    job_id INTEGER NOT NULL
        REFERENCES jobs(id) ON DELETE CASCADE,
    trait_id INTEGER NOT NULL
        REFERENCES traits(id) ON DELETE RESTRICT,
    PRIMARY KEY (job_id, trait_id)
);

CREATE INDEX IF NOT EXISTS idx_candidate_skills_skill_id
    ON candidate_skills(skill_id);

CREATE INDEX IF NOT EXISTS idx_job_skills_skill_id
    ON job_skills(skill_id);

CREATE INDEX IF NOT EXISTS idx_candidate_traits_trait_id
    ON candidate_traits(trait_id);

CREATE INDEX IF NOT EXISTS idx_job_culture_trait_id
    ON job_culture(trait_id);
