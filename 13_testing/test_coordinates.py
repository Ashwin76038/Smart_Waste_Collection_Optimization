def test_bin_coordinates_within_chennai_and_unique_road_nodes(db):
    row=db.execute('''SELECT COUNT(*), COUNT(DISTINCT osm_node_id),
        COUNT(*) FILTER (WHERE latitude NOT BETWEEN 12.9 AND 13.25
                          OR longitude NOT BETWEEN 80.15 AND 80.38)
        FROM dim_bin''').fetchone()
    assert row==(1000,1000,0)

def test_each_bin_on_extracted_osm_node(db):
    assert db.execute('SELECT COUNT(*) FROM dim_bin b ANTI JOIN osm_road_nodes_chennai n USING (osm_node_id)').fetchone()[0]==0
