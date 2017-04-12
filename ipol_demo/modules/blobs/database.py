from errors import IPOLBlobsDataBaseError


def get_blob_tags(conn, blob_hash):
    """
    returns the list of tags for the blob
    """
    cursor = conn.cursor()
    cursor.execute("""
    SELECT name
    FROM tags,blobs_tags,blobs
    WHERE hash = ?
    AND blob_id = blobs.id
    AND tag_id = tags.id
    """, (blob_hash,))
    tags = []
    for tag in cursor.fetchall():
        tags.append(tag[0])

    return tags


def store_blob(conn, blob_hash, blob_format, extension, title, credit):
    """
    Store the blob in the Blobs table
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO blobs (hash, format, extension, title, credit)
            VALUES (?,?,?,?,?)
            """, (blob_hash, blob_format, extension, title, credit))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def is_blob_in_db(conn, blob_hash):
    """
    Verify if the hash is already stored in the DB
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS(SELECT *
                        FROM blobs
                        WHERE hash=?);
            """, (blob_hash,))
        return cursor.fetchone()[0] == 1
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def demo_exist(conn, editor_demo_id):
    """
    Verify if the editor_demo_id references an existing demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS(SELECT *
                        FROM demos
                        WHERE editor_demo_id=?);
            """, (editor_demo_id,))
        return cursor.fetchone()[0] == 1
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def create_demo(conn, editor_demo_id):
    """
    Creates a new demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO demos (editor_demo_id)
            VALUES (?)
            """, (editor_demo_id,))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def add_blob_to_demo(conn, editor_demo_id, blob_hash, blob_set, blob_pos):
    """
    Associates the blob to a demo in demos_blobs table
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO demos_blobs (demo_id, blob_id, blob_set, pos_in_set)
            VALUES ((SELECT id
                    FROM demos
                    WHERE editor_demo_id = ?),(SELECT id
                                                FROM blobs
                                                WHERE hash = ?),?,?)
            """, (editor_demo_id, blob_hash, blob_set, blob_pos))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def all_templates_exist(conn, template_names):
    """
    Verify if ALL the template_names references an existing template
    """
    try:
        for name in template_names:
            if not template_exist(conn, name):
                return False
        return True
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def template_exist(conn, template_name):
    """
    Verify if the template_name references an existing template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
                SELECT COUNT(*)
                FROM templates
                WHERE name = ?
                """, (template_name,))
        return cursor.fetchone()[0] >= 1
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def create_template(conn, template_name):
    """
    Creates a new template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO templates (name)
            VALUES (?)
            """, (template_name,))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def add_blob_to_template(conn, template_name, blob_hash, pos_set, blob_set):
    """
    Associates the blob to a template in templates_blobs table
    """
    print template_name, blob_hash, pos_set, blob_set
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO templates_blobs (template_id, blob_id, blob_set, pos_in_set)
            VALUES ((SELECT id
                    FROM templates
                    WHERE name = ?),(SELECT id
                                    FROM blobs
                                    WHERE hash = ?),?,?)
            """, (template_name, blob_hash, blob_set, pos_set))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def create_tags(conn, tags):
    """
    Creates the tags
    """
    try:
        cursor = conn.cursor()
        for tag in tags:
            if tag == "":
                continue

            # Check if the tag already exists
            cursor.execute("""
                        SELECT EXISTS(SELECT *
                                    FROM tags
                                    WHERE name=?);
                        """, (tag,))

            if cursor.fetchone()[0] == 1:
                continue

            cursor.execute("""
                        INSERT INTO tags (name)
                        VALUES (?)
                        """, (tag,))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def add_tags_to_blob(conn, tags, blob_hash):
    """
    Associates all the tags to a blob in tags_blobs table
    """
    try:
        cursor = conn.cursor()
        for tag in tags:
            cursor.execute("""
                    SELECT EXISTS(SELECT *
                                FROM blobs_tags
                                WHERE tag_id=(SELECT id
                                            FROM tags
                                            WHERE name=?)
                                AND blob_id=(SELECT id
                                            FROM blobs
                                            WHERE hash=?));
                    """, (tag, blob_hash))

            if cursor.fetchone()[0] == 1:
                continue

            cursor.execute("""
                INSERT INTO blobs_tags (blob_id, tag_id)
                VALUES ((SELECT id
                        FROM blobs
                        WHERE hash = ?),(SELECT id
                                        FROM tags
                                        WHERE name = ?))
                """, (blob_hash, tag))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def add_templates_to_demo(conn, template_names, editor_demo_id):
    """
    Associates all the templates to the demo in demos_templates table
    """
    try:
        cursor = conn.cursor()
        for name in template_names:
            cursor.execute("""
                    SELECT EXISTS(SELECT *
                                FROM demos_templates
                                WHERE demo_id=(SELECT id
                                            FROM demos
                                            WHERE editor_demo_id=?)
                                AND template_id=(SELECT id
                                                FROM templates
                                                WHERE name=?));
                    """, (editor_demo_id, name))

            if cursor.fetchone()[0] == 1:
                continue

            cursor.execute("""
                            INSERT INTO demos_templates (demo_id, template_id)
                            VALUES ((SELECT id
                                    FROM demos
                                    WHERE editor_demo_id = ?),(SELECT id
                                                    FROM templates
                                                    WHERE name = ?))
                                                    """, (editor_demo_id, name))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_demo_owned_blobs(conn, editor_demo_id):
    """
    Get all the blobs owned by the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hash, format, extension, title, credit, blob_set, pos_in_set
            FROM blobs, demos, demos_blobs
            WHERE demo_id = demos.id
            AND blob_id = blobs.id
            AND demos.editor_demo_id = ?
            """, (editor_demo_id,))
        blobs = []
        for row in cursor.fetchall():
            blobs.append({"hash": row[0], "format": row[1], "extension": row[2], "title": row[3], "credit": row[4],
                          "blob_set": row[5], "pos_set": row[6], "tags": get_blob_tags(conn, row[0])})

        return blobs
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_template_blobs(conn, name):
    """
    Get all the blobs owned by the template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hash, format, extension, title, credit, blob_set, pos_in_set
            FROM blobs, templates, templates_blobs
            WHERE template_id = templates.id
            AND blob_id = blobs.id
            AND templates.name = ?
            """, (name,))
        blobs = []
        for row in cursor.fetchall():
            blobs.append({"hash": row[0], "format": row[1], "extension": row[2], "title": row[3], "credit": row[4],
                          "blob_set": row[5], "pos_set": row[6], "tags": get_blob_tags(conn, row[0])})
        return blobs
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_demo_templates(conn, editor_demo_id):
    """
    Get all the templates owned by the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name
            FROM templates
            WHERE id IN (SELECT template_id
                        FROM demos_templates
                        WHERE demo_id = (SELECT id
                                        FROM demos
                                        WHERE editor_demo_id = ?))
            """, (editor_demo_id,))
        templates = []
        for row in cursor.fetchall():
            templates.append(row[0])
        return templates
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_blob_data_from_demo(conn, editor_demo_id, blob_set, pos_set):
    """
    Return the blob data from the position of the set in the demo or
    None if there is not blob for the given parameters
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hash, format, extension, title, credit
            FROM blobs, demos_blobs, demos
            WHERE editor_demo_id = ?
            AND blob_set = ?
            AND pos_in_set = ?
            AND demo_id = demos.id
            AND blobs.id = blob_id
            """, (editor_demo_id, blob_set, pos_set))
        data = cursor.fetchone()
        if data is None:
            return None
        result = {'hash': data[0], 'format': data[1], 'extension': data[2], 'title': data[3], 'credit': data[4]}
        return result
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_blob_data_from_template(conn, template_name, blob_set, pos_set):
    """
    Return the blob data from the position of the set in the template or
    None if there is not blob for the given parameters
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hash, format, extension, title, credit
            FROM blobs, templates_blobs, templates
            WHERE name = ?
            AND blob_set = ?
            AND pos_in_set = ?
            AND template_id = templates.id
            AND blobs.id = blob_id
            """, (template_name, blob_set, pos_set))
        data = cursor.fetchone()
        if data is None:
            return None
        result = {'hash': data[0], 'format': data[1], 'extension': data[2], 'title': data[3], 'credit': data[4]}
        return result

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_blob_from_demo(conn, editor_demo_id, blob_set, pos_set):
    """
    Remove the blob from the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
                DELETE
                FROM demos_blobs
                WHERE demo_id = (SELECT id
                                FROM demos
                                WHERE editor_demo_id = ?)
                AND blob_set = ?
                AND pos_in_set = ?
                """, (editor_demo_id, blob_set, pos_set))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_blob_from_template(conn, template_name, blob_set, pos_set):
    """
    Remove the blob from the template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
                DELETE
                FROM templates_blobs
                WHERE template_id = (SELECT id
                                FROM templates
                                WHERE name = ?)
                AND blob_set = ?
                AND pos_in_set = ?
                """, (template_name, blob_set, pos_set))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def is_blob_used(conn, blob_hash):
    """
    Check if the blob is being used in any demo or template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM blobs
            WHERE (id IN (SELECT blob_id FROM templates_blobs) OR
                   id IN(SELECT blob_id FROM demos_blobs))
            AND hash = ?
                """, (blob_hash,))
        return cursor.fetchone()[0] >= 1

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_blob(conn, blob_hash):
    """
    Remove the blob from the DB and its tags
    """
    try:
        cursor = conn.cursor()
        tags = get_blob_tags(conn, blob_hash)

        cursor.execute("""PRAGMA foreign_keys = ON""")
        cursor.execute("""
            DELETE
            FROM blobs
            WHERE hash = ?
            """, (blob_hash,))

        for tag in tags:
            if not tag_is_used(conn, tag):
                remove_tag(conn, tag)

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_demo(conn, editor_demo_id):
    """
    Remove the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
            DELETE
            FROM demos
            WHERE editor_demo_id = ?
            """, (editor_demo_id,))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_template(conn, template_name):
    """
    Remove the template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
            DELETE
            FROM templates
            WHERE name = ?
            """, (template_name,))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_demo_blobs_association(conn, editor_demo_id):
    """
    Remove association between blobs and the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
            DELETE
            FROM demos_blobs
            WHERE demo_id = (SELECT id
                            FROM demos
                            WHERE editor_demo_id = ?)
            """, (editor_demo_id,))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_template_blobs_association(conn, template_name):
    """
    Remove association between blobs and the template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
            DELETE
            FROM templates_blobs
            WHERE template_id = (SELECT id
                            FROM templates
                            WHERE name = ?)
            """, (template_name,))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_template_from_demo(conn, editor_demo_id, template_name):
    """
    Remove the template from the demo in the demos_template table
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
            DELETE
            FROM demos_templates
            WHERE demo_id = (SELECT id
                            FROM demos
                            WHERE editor_demo_id = ?)
            AND template_id = (SELECT id
                            FROM templates
                            WHERE name = ?)
            """, (editor_demo_id, template_name))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_tag_from_demo(conn, tag, editor_demo_id, blob_set, pos_set):
    """
    Remove tag from demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
            DELETE
            FROM blobs_tags
            WHERE  tag_id = (SELECT id
                            FROM tags
                            WHERE name = ?)
            AND blob_id = (SELECT blob_id
                            FROM demos, demos_blobs
                            WHERE editor_demo_id = ?
                            AND blob_set = ?
                            AND pos_in_set = ? )
            """, (tag, editor_demo_id, blob_set, pos_set))
        if not tag_is_used(conn, (tag,)):
            remove_tag(conn, (tag,))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_tag_from_template(conn, tag, template_name, blob_set, pos_set):
    """
    Remove tag from template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
            DELETE
            FROM blobs_tags
            WHERE  tag_id = (SELECT id
                            FROM tags
                            WHERE name = ?)
            AND blob_id = (SELECT blob_id
                            FROM templates, templates_blobs
                            WHERE name = ?
                            AND blob_set = ?
                            AND pos_in_set = ? )
            """, (tag, template_name, blob_set, pos_set))

        if not tag_is_used(conn, (tag,)):
            remove_tag(conn, (tag,))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def tag_is_used(conn, tag):
    """
    Check if the tag is being used in any blob
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM tags
            WHERE tags.name = ?
            AND id IN (SELECT tag_id
                       FROM blobs_tags)
            """, (tag,))
        return cursor.fetchone()[0] >= 1

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_tag(conn, tag):
    """
    Remove the tag
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE
            FROM tags
            WHERE name = ?
            """, (tag,))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def edit_blob_from_demo(conn, editor_demo_id, set_name, new_set_name, pos, new_pos, title, credit):
    """
    Edit information of the blob in a demo
    """
    try:
        cursor = conn.cursor()

        # Change title and credit from blobs table
        cursor.execute("""
            UPDATE blobs
            SET title = ?, credit = ?
            WHERE id = (SELECT blob_id
                        FROM demos, demos_blobs
                        WHERE demos.id = demo_id
                        AND editor_demo_id= ?
                        AND blob_set = ?
                        AND pos_in_set = ?)
            """, (title, credit, editor_demo_id, set_name, pos))

        # Change set and pos from demos_blobs table
        cursor.execute("""
            UPDATE demos_blobs
            SET blob_set = ?, pos_in_set = ?
            WHERE blob_set = ?
            AND pos_in_set = ?
            AND demo_id = (SELECT id
                            FROM demos
                            WHERE editor_demo_id = ?)
            """, (new_set_name, new_pos, set_name, pos, editor_demo_id))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def edit_blob_from_template(conn, template_name, set_name, new_set_name, pos, new_pos, title, credit):
    """
    Edit information of the blob in a template
    """
    try:
        cursor = conn.cursor()

        # Change title and credit from blobs table
        cursor.execute("""
            UPDATE blobs
            SET title = ?, credit = ?
            WHERE id = (SELECT blob_id
                        FROM templates, templates_blobs
                        WHERE templates.id = template_id
                        AND templates.name= ?
                        AND blob_set = ?
                        AND pos_in_set = ?)
            """, (title, credit, template_name, set_name, pos))

        # Change set and pos from templates_blobs table
        cursor.execute("""
            UPDATE templates_blobs
            SET blob_set = ?, pos_in_set = ?
            WHERE blob_set = ?
            AND pos_in_set = ?
            AND template_id = (SELECT id
                                FROM templates
                                WHERE name = ?)
            """, (new_set_name, new_pos, set_name, pos, template_name))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def is_pos_occupied_in_demo_set(conn, editor_demo_id, blob_set, pos):
    """
    Check if the position given is already used by other blob in the same set
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM demos_blobs
            WHERE blob_set = ?
            AND pos_in_set = ?
            AND demo_id = (SELECT id
                            FROM demos
                            WHERE editor_demo_id = ?)
        """, (blob_set, pos, editor_demo_id))

        return cursor.fetchone()[0] >= 1

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def is_pos_occupied_in_template_set(conn, template_name, blob_set, pos):
    """
    Check if the position given is already used by other blob in the same set
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM templates_blobs
            WHERE blob_set = ?
            AND pos_in_set = ?
            AND template_id = (SELECT id
                               FROM templates
                               WHERE name = ?)
        """, (blob_set, pos, template_name))

        return cursor.fetchone()[0] >= 1

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_max_pos_in_demo_set(conn, editor_demo_id, blob_set):
    """
    Return the max position value of the set in the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MAX(pos_in_set)
            FROM demos_blobs
            WHERE blob_set = ?
            AND demo_id = (SELECT id
                            FROM demos
                            WHERE editor_demo_id = ?)
        """, (blob_set, editor_demo_id))

        return cursor.fetchone()[0]

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_max_pos_in_template_set(conn, template_name, blob_set):
    """
    Return the max position value of the set in the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MAX(pos_in_set)
            FROM templates_blobs
            WHERE blob_set = ?
            AND template_id = (SELECT id
                            FROM templates
                            WHERE name = ?)
        """, (blob_set, template_name))

        return cursor.fetchone()[0]

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_all_templates(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name
            FROM templates
            """)
        templates = []
        for row in cursor.fetchall():
            templates.append(row[0])
        return templates
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def update_demo_id(conn, old_editor_demo_id, new_editor_demo_id):
    """
    Update the given old editor demo id by the given new editor demo id
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE demos
            SET editor_demo_id = ?
            WHERE editor_demo_id = ?
            """, (new_editor_demo_id, old_editor_demo_id))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


# ----------- DEPRECATED FUNCTIONS ---------------
# This functions are for the OLD web interface and
# they shouldn't be called by new methods.
# [TODO] Get rid of these functions

def get_demo_owned_blobs_deprecated(conn, editor_demo_id):
    """
    Get all the blobs owned by the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hash, format, extension, title, credit, blob_set, pos_in_set, blobs.id
            FROM blobs, demos, demos_blobs
            WHERE demo_id = demos.id
            AND blob_id = blobs.id
            AND demos.editor_demo_id = ?
            """, (editor_demo_id,))
        blobs = []
        for row in cursor.fetchall():
            blobs.append({"hash": row[0], "format": row[1], "extension": row[2], "title": row[3], "credit": row[4],
                          "blob_set": row[5], "pos_set": row[6], "id": row[7], "tags": get_blob_tags(conn, row[0])})

        return blobs
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_template_blobs_deprecated(conn, name):
    """
    Get all the blobs owned by the template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hash, format, extension, title, credit, blob_set, pos_in_set, blobs.id
            FROM blobs, templates, templates_blobs
            WHERE template_id = templates.id
            AND blob_id = blobs.id
            AND templates.name = ?
            """, (name,))
        blobs = []
        for row in cursor.fetchall():
            blobs.append({"hash": row[0], "format": row[1], "extension": row[2], "title": row[3], "credit": row[4],
                          "blob_set": row[5], "pos_set": row[6], "id": row[7], "tags": get_blob_tags(conn, row[0])})
        return blobs
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_blob_data_deprecated(conn, blob_id):
    """
    Return the blob data from the position of the set in the demo or
    None if there is not blob for the given parameters
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hash, format, extension, title, credit
            FROM blobs
            WHERE id = ?
            """, (blob_id,))
        data = cursor.fetchone()
        if data is None:
            return None
        result = {'hash': data[0], 'format': data[1], 'extension': data[2], 'title': data[3], 'credit': data[4]}
        return result
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)
