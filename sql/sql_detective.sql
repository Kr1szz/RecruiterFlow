-- Question 1: Open postings and their recruiter.
SELECT jp.id, jp.title, r.name AS recruiter_name
FROM job_postings AS jp
JOIN recruiters AS r ON r.id = jp.recruiter_id
WHERE jp.status = 'open'
ORDER BY jp.id;

-- Question 2: Number of applicants who reached the Final stage for every posting.
SELECT jp.id, jp.title,
       COUNT(DISTINCT i.applicant_id) FILTER (WHERE i.stage = 'Final') AS final_stage_applicants
FROM job_postings AS jp
LEFT JOIN interviews AS i ON i.job_posting_id = jp.id
GROUP BY jp.id, jp.title
ORDER BY jp.id;

-- Question 3: People applied to more than one posting. Normalize email case/whitespace
-- to identify the duplicated Ananya Rao records as the same person. applicants has no
-- posting column, so "applied to a posting" is inferred from the interviews table.
SELECT MIN(a.full_name) AS person_name,
       LOWER(BTRIM(a.email)) AS normalized_email,
       COUNT(DISTINCT i.job_posting_id) AS distinct_job_postings
FROM applicants AS a
JOIN interviews AS i ON i.applicant_id = a.id
WHERE a.email IS NOT NULL
GROUP BY LOWER(BTRIM(a.email))
HAVING COUNT(DISTINCT i.job_posting_id) > 1
ORDER BY normalized_email;

-- Question 4: Final-stage pass rate for recruiters with at least three Final interviews.
SELECT r.id, r.name,
       COUNT(*) FILTER (WHERE i.outcome = 'passed') AS final_passes,
       COUNT(*) AS final_interviews,
       ROUND(COUNT(*) FILTER (WHERE i.outcome = 'passed')::numeric / COUNT(*), 2) AS conversion_rate
FROM recruiters AS r
JOIN job_postings AS jp ON jp.recruiter_id = r.id
JOIN interviews AS i ON i.job_posting_id = jp.id AND i.stage = 'Final'
GROUP BY r.id, r.name
HAVING COUNT(*) >= 3
ORDER BY r.id;

-- Question 5 (bonus): The recruiter with the most successful Final placements in each
-- department. ROW_NUMBER keeps exactly one per department; ties go to the lower recruiter ID.
WITH recruiter_placements AS (
    SELECT jp.department, r.id AS recruiter_id, r.name AS recruiter_name,
           COUNT(i.id) FILTER (WHERE i.stage = 'Final' AND i.outcome = 'passed') AS successful_placements
    FROM job_postings AS jp
    JOIN recruiters AS r ON r.id = jp.recruiter_id
    LEFT JOIN interviews AS i ON i.job_posting_id = jp.id
    GROUP BY jp.department, r.id, r.name
), ranked AS (
    SELECT department, recruiter_id, recruiter_name, successful_placements,
           ROW_NUMBER() OVER (
               PARTITION BY department
               ORDER BY successful_placements DESC, recruiter_id
           ) AS department_rank
    FROM recruiter_placements
)
SELECT department, recruiter_id, recruiter_name, successful_placements
FROM ranked
WHERE department_rank = 1
ORDER BY department;
