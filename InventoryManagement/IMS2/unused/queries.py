

sku_query = """
    SELECT
        s.sku_id, s.sku_valid, s.bit_code, s.sku_qty, s.min_qty,
        s.item_id, s.item_size_id, s.item_side_id, s.expiration_date,
        i.item_name, isz.item_size, isd.item_side
    FROM skus AS s
    JOIN items AS i USING(item_id)
    JOIN item_size AS isz USING(item_size_id)
    JOIN item_side AS isd USING(item_side_id)
"""

transaction_query = """
    SELECT 
        t.tr_id, t.user_id, t.sku_id, t.tr_type_id, t.tr_qty,
        t.before_qty, t.after_qty, t.tr_timestamp, tt.tr_type,
        i.item_name, isz.item_size, isd.item_side, u.user_name, 
    FROM transactions AS t
    JOIN skus AS s USING(sku_id)
    JOIN items AS i USING(item_id)
    JOIN transaction_type AS tt USING(tr_type_id)
    JOIN item_size AS isz USING(item_size_id)
    JOIN item_side AS isd USING(item_side_id)
    JOIN users As u USING(user_id)
"""
