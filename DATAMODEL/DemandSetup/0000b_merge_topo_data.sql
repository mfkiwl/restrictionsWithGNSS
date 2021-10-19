-- Merge with different datasets

-- topography.os_mastermap_topography_polygons and topography.os_mastermap_topography_polygons2

DELETE
FROM topography.os_mastermap_topography_polygons2 t2
WHERE  RIGHT(fid, LENGTH(fid) - 4)::bigint in (SELECT toid
					                           FROM topography.os_mastermap_topography_polygons);

INSERT INTO topography.os_mastermap_topography_polygons(
	id, geom, toid, "FeatureCode", "Version", "VersionDate", "Theme", "CalculatedAreaValue", "ChangeDate", "ReasonForChange", "DescriptiveGroup", "DescriptiveTerm", "Make", "PhysicalLevel")

SELECT id, geom,  RIGHT(fid, LENGTH(fid) - 4)::bigint, "featureCode", version, "versionDate", theme, "calculatedAreaValue", "changeDate", "reasonForChange", "descriptiveGroup", "descriptiveTerm", make, "physicalLevel"
	FROM topography.os_mastermap_topography_polygons2;

-- topography.os_mastermap_topography_text and topography.os_mastermap_topography_text2

DELETE
FROM topography.os_mastermap_topography_text2 t2
WHERE  RIGHT(fid, LENGTH(fid) - 4)::bigint in (SELECT toid
					                           FROM topography.os_mastermap_topography_text);

INSERT INTO topography.os_mastermap_topography_text(
	id, geom, toid, "FeatureCode", "Version", "VersionDate", "Theme", "ChangeDate", "ReasonForChange", "DescriptiveGroup", "DescriptiveTerm", "Make", "PhysicalLevel", "AnchorPosition", "Font", xml_text_size, xml_rotation, xml_text_string)

SELECT id, geom, RIGHT(fid, LENGTH(fid) - 4)::bigint, "featureCode", version, "versionDate", theme, "changeDate", "reasonForChange", "descriptiveGroup", "descriptiveTerm", make, "physicalLevel", "anchorPosition", font, height, orientation, "textString"
	FROM topography.os_mastermap_topography_text2;