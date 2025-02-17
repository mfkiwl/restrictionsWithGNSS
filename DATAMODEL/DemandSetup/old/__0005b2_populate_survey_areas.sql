--

UPDATE "mhtc_operations"."Supply" AS s
SET "SurveyAreaID" = a."Code"
FROM mhtc_operations."SurveyAreas" a
WHERE ST_WITHIN (s.geom, a.geom);

ALTER TABLE IF EXISTS mhtc_operations."RC_Sections_merged"
  ADD COLUMN IF NOT EXISTS "SurveyAreaID" INTEGER;

UPDATE mhtc_operations."RC_Sections_merged"
SET "SurveyAreaID" = NULL;

UPDATE "mhtc_operations"."RC_Sections_merged" AS s
SET "SurveyAreaID" = a."Code"
FROM mhtc_operations."SurveyAreas" a
WHERE ST_WITHIN (s.geom, a.geom);

/***
 Plans for all survey areas for all survey times

DROP TABLE IF EXISTS mhtc_operations."SupplyPlansList";

CREATE TABLE mhtc_operations."SupplyPlansList" (
    id SERIAL,
    "SurveyID" integer NOT NULL,
	"SurveyDate" DATE NOT NULL DEFAULT CURRENT_DATE,
    "BeatStartTime" character varying (10) COLLATE pg_catalog."default",
    "BeatEndTime" character varying (10) COLLATE pg_catalog."default",
    "SurveyArea" character varying(32) COLLATE pg_catalog."default",
    geom geometry(MultiPolygon,27700),
    "SupplyPlanName" character varying(50) COLLATE pg_catalog."default",
    CONSTRAINT "SupplyPlansList_pkey" PRIMARY KEY (id)
);

INSERT INTO mhtc_operations."SupplyPlansList" (
    "SurveyID", "SurveyDate", "BeatStartTime", "BeatEndTime", "SurveyArea", geom, "SupplyPlanName"
)
SELECT s."SurveyID", s."SurveyDate", s."BeatStartTime", s."BeatEndTime", sa."name", sa.geom, CONCAT('Area_', sa."name", '_', s."BeatTitle") AS "SurveyName"
	FROM demand."Surveys" s, mhtc_operations."SurveyAreas" sa
	ORDER BY "SurveyName";
***/

/***
 Changes to new structure


ALTER TABLE IF EXISTS mhtc_operations."SurveyAreas"
    RENAME id TO "Code";

ALTER TABLE IF EXISTS mhtc_operations."SurveyAreas"
    RENAME name TO "SurveyAreaName";

ALTER TABLE mhtc_operations."SurveyAreas"
    ALTER COLUMN "SurveyAreaName" TYPE character varying(250) COLLATE pg_catalog."default";

-- if required ...
UPDATE "mhtc_operations"."Supply" AS s
SET "SurveyAreaID" = a."Code"
FROM mhtc_operations."SurveyAreas" a
WHERE ST_WITHIN (s.geom, a.geom);

ALTER TABLE IF EXISTS mhtc_operations."Supply"
    RENAME "SurveyArea" TO "SurveyAreaID";

alter table mhtc_operations."Supply" alter column "SurveyAreaID" TYPE INTEGER  USING ("SurveyAreaID"::integer) ;

 ***/

/***

--
-- Calculate length of section within area

UPDATE "mhtc_operations"."RC_Sections_merged" AS s
SET "SurveyAreaID" = a."Code"
FROM mhtc_operations."SurveyAreas" a
WHERE ST_WITHIN (s.geom, a.geom);

SELECT a."SurveyAreaName", SUM(s."SectionLength")
FROM mhtc_operations."RC_Sections_merged" s, mhtc_operations."SurveyAreas" a
WHERE ST_WITHIN (s.geom, a.geom)
GROUP BY a."SurveyAreaName"
ORDER BY a."SurveyAreaName";

-- OR

UPDATE "mhtc_operations"."Supply" AS s
SET "SurveyAreaID" = NULL;

UPDATE "mhtc_operations"."Supply" AS s
SET "SurveyAreaID" = a."Code"
FROM mhtc_operations."SurveyAreas" a
WHERE ST_WITHIN (s.geom, a.geom);

SELECT a."SurveyAreaName", SUM(s."RestrictionLength") AS "RestrictionLength", SUM("Capacity") AS "Total Capacity",
SUM (CASE WHEN "RestrictionTypeID" > 200 THEN 0 ELSE s."Capacity" END) AS "Bay Capacity"
FROM mhtc_operations."Supply" s, mhtc_operations."SurveyAreas" a
WHERE a."Code" = s."SurveyAreaID"
--AND a."SurveyAreaName" LIKE 'V%'
GROUP BY a."SurveyAreaName"
ORDER BY a."SurveyAreaName";
***/
-- CPZs
/***
SELECT a."CPZ", SUM(s."RestrictionLength") AS "RestrictionLength", SUM("Capacity") AS "Total Capacity",
SUM (CASE WHEN s."RestrictionTypeID" > 200 THEN 0 ELSE s."Capacity" END) AS "Bay Capacity"
FROM mhtc_operations."Supply" s, toms."ControlledParkingZones" a
WHERE ST_WITHIN (s.geom, a.geom)
--AND a."SurveyAreaName" LIKE 'V%'
GROUP BY a."CPZ"
ORDER BY a."CPZ";
***/

