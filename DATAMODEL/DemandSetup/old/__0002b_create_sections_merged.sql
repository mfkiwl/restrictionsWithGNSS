--	Merge sections that are broken

DROP TABLE IF EXISTS "mhtc_operations"."RC_Sections_merged" CASCADE;

CREATE TABLE "mhtc_operations"."RC_Sections_merged"
(
  gid SERIAL,
  geom geometry(LineString,27700),
  "RoadName" character varying(100),
  "USRN" bigint,
  "Az" double precision,
  "StartStreet" character varying(254),
  "EndStreet" character varying(254),
  "SideOfStreet" character varying(100),
  CONSTRAINT "RC_Sections_merged_pkey" PRIMARY KEY (gid)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE "mhtc_operations"."RC_Sections_merged"
  OWNER TO postgres;

-- Index: public."sidx_RC_Sections_merged_geom"

-- DROP INDEX public."sidx_RC_Sections_merged_geom";

CREATE INDEX "sidx_RC_Sections_merged_geom"
  ON "mhtc_operations"."RC_Sections_merged"
  USING gist
  (geom);

INSERT INTO "mhtc_operations"."RC_Sections_merged" (geom)
SELECT (ST_Dump(ST_LineMerge(ST_Collect(a.geom)))).geom As geom
FROM "mhtc_operations"."RC_Sections" as a
LEFT JOIN "mhtc_operations"."RC_Sections" as b ON
ST_Touches(a.geom,b.geom)
GROUP BY ST_Touches(a.geom,b.geom);

DROP FUNCTION IF EXISTS mhtc_operations."get_nearest_roadlink_to_section"(section_id integer);
CREATE OR REPLACE FUNCTION mhtc_operations."get_nearest_roadlink_to_section"(section_id integer)
    RETURNS text[]
    LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
	 roadlink_id integer;
	 closest_pt_wkt text;
	 details text[] := ARRAY[]::TEXT[];
BEGIN

    -- find nearest junction

    SELECT cl."id", ST_AsText(ST_ClosestPoint(ST_LineInterpolatePoint(s.geom, 0.5), cl.geom))
	INTO roadlink_id, closest_pt_wkt
    FROM "highways_network"."roadlink" cl, "mhtc_operations"."RC_Sections_merged" s
    WHERE s.gid = section_id
    AND ST_DWithin(ST_LineInterpolatePoint(s.geom, 0.5), ST_ClosestPoint(ST_LineInterpolatePoint(s.geom, 0.5), cl.geom), 30.0)
    ORDER BY
      ST_Distance(ST_LineInterpolatePoint(s.geom, 0.5), ST_ClosestPoint(ST_LineInterpolatePoint(s.geom, 0.5), cl.geom))
    LIMIT 1;


    SELECT ARRAY[roadlink_id::TEXT, closest_pt_wkt] INTO details;

    RETURN details;

END;
$BODY$;

/*
UPDATE "mhtc_operations"."RC_Sections_merged" AS c
SET "RoadName" = r."name1", "USRN" = r."localid",
    "Az" = ST_Azimuth(ST_LineInterpolatePoint(c.geom, 0.5), ST_GeomFromText((mhtc_operations."get_nearest_roadlink_to_section"(c.gid))[2], 27700)),
    "StartStreet" = r."RoadFrom", "EndStreet" = r."RoadTo"
FROM "highways_network"."roadlink" r
WHERE r."id" = (mhtc_operations."get_nearest_roadlink_to_section"(c.gid))[1]::integer;
*/

UPDATE "mhtc_operations"."RC_Sections_merged" AS c
SET "RoadName" = closest."RoadName", --"USRN" = closest."USRN",
	"Az" = ST_Azimuth(ST_LineInterpolatePoint(c.geom, 0.5), closest.geom), "StartStreet" = closest."RoadFrom", "EndStreet" = closest."RoadTo"
FROM (SELECT DISTINCT ON (s."gid") s."gid" AS id, 
    cl."name1" AS "RoadName", 
	-- cl."roadName1_Name" AS "RoadName",
    ST_ClosestPoint(cl.geom, ST_LineInterpolatePoint(s.geom, 0.5)) AS geom, ST_Distance(cl.geom, ST_LineInterpolatePoint(s.geom, 0.5)) AS length, cl."RoadFrom", cl."RoadTo"
      FROM "highways_network"."roadlink" cl, "mhtc_operations"."RC_Sections_merged" s
	  WHERE cl."name1" IS NOT NULL
	  --WHERE LENGTH(cl."roadName1_Name") > 0
      ORDER BY s."gid", length) AS closest
WHERE c."gid" = closest.id
AND closest."RoadName" NOT LIKE '% Car Park%';

UPDATE "mhtc_operations"."RC_Sections_merged"
SET "SideOfStreet" = 'North'
WHERE degrees("Az") > 135.0
AND degrees("Az") <= 225.0;

UPDATE "mhtc_operations"."RC_Sections_merged"
SET "SideOfStreet" = 'South'
WHERE degrees("Az") > 315.0
OR  degrees("Az") <= 45.0;

UPDATE "mhtc_operations"."RC_Sections_merged"
SET "SideOfStreet" = 'East'
WHERE degrees("Az") > 225.0
AND degrees("Az") <= 315.0;

UPDATE "mhtc_operations"."RC_Sections_merged"
SET "SideOfStreet" = 'West'
WHERE degrees("Az") > 45.0
AND degrees("Az") <= 135.0;

--

CREATE OR REPLACE FUNCTION "mhtc_operations".set_section_length()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
    BEGIN
	    -- round to two decimal places
        NEW."SectionLength" := ROUND(public.ST_Length (NEW."geom")::numeric,2);

        RETURN NEW;
    END;
$BODY$;

ALTER FUNCTION "mhtc_operations".set_section_length()
    OWNER TO postgres;

ALTER TABLE "mhtc_operations"."RC_Sections_merged"
    ADD COLUMN IF NOT EXISTS "SectionLength" double precision;

DROP TRIGGER IF EXISTS "set_section_length"ON "mhtc_operations"."RC_Sections_merged";

CREATE TRIGGER "set_section_length"
    BEFORE INSERT OR UPDATE
    ON "mhtc_operations"."RC_Sections_merged"
    FOR EACH ROW
    EXECUTE PROCEDURE "mhtc_operations".set_section_length();

-- trigger trigger
UPDATE "mhtc_operations"."RC_Sections_merged" SET "SectionLength" = "SectionLength";
ALTER TABLE "mhtc_operations"."RC_Sections_merged" ALTER COLUMN "SectionLength" SET NOT NULL;

ALTER TABLE "mhtc_operations"."RC_Sections_merged"
    ADD COLUMN IF NOT EXISTS "Photos_01" character varying(255);
ALTER TABLE "mhtc_operations"."RC_Sections_merged"
    ADD COLUMN IF NOT EXISTS "Photos_02" character varying(255);
ALTER TABLE "mhtc_operations"."RC_Sections_merged"
    ADD COLUMN IF NOT EXISTS "Photos_03" character varying(255);

-- set up names for sections

ALTER TABLE mhtc_operations."RC_Sections_merged" ADD COLUMN IF NOT EXISTS "SectionName" character varying(254);

/***
SELECT gid, geom, "RoadName", "Az", "StartStreet", "EndStreet", "SideOfStreet", "SurveyArea", "SectionName", n."SubID", n."SectionID", n."Road Name", n."Section Start", n."Section End", n."Section Side of Street"
	FROM mhtc_operations."RC_Sections_merged" s, mhtc_operations."SectionNames" n
	WHERE n."SubID" = s.gid
***/

WITH section_details AS (
    SELECT gid,
	"RoadName",
	UPPER(CONCAT(REPLACE("RoadName", ' ', '_'), '_', to_char(ROW_NUMBER () OVER (
                                                             PARTITION BY "RoadName"
                                                             ORDER BY "RoadName"
                                                            ), 'FM000'))) AS "SectionName"
	FROM mhtc_operations."RC_Sections_merged"
        )

UPDATE mhtc_operations."RC_Sections_merged" s
SET "SectionName" = n."SectionName"
FROM section_details n
WHERE n.gid = s.gid
;

GRANT SELECT ON TABLE "mhtc_operations"."RC_Sections_merged" TO toms_admin, toms_operator;
