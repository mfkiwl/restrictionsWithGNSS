/**
 Include only required sign types
**/

DELETE FROM toms_lookups."SignTypesInUse";

INSERT INTO toms_lookups."SignTypesInUse"("Code")
    SELECT "Code"
	FROM toms_lookups."SignTypes"
	WHERE "Description" LIKE ('Parking%')
	OR "Description" LIKE ('Parking%')
	OR "Code" IN (0, 37, 9999)
	ORDER BY "Description";

REFRESH MATERIALIZED VIEW "toms_lookups"."SignTypesInUse_View";

/**
Ensure appropriate bay/line types
**/

INSERT INTO toms_lookups."LineTypesInUse"(
	"Code", "GeomShapeGroupType")
	VALUES (225, 'LineString');  -- Unmarked kerbline

REFRESH MATERIALIZED VIEW "toms_lookups"."LineTypesInUse_View";