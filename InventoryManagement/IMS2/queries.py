

sku_query = """
    SELECT
        s.sku_id, s.sku_qty, s.min_qty, i.item_name,
        isz.item_size, isd.item_side
    FROM skus AS s
    JOIN items AS i USING(item_id)
    JOIN item_size AS isz USING(item_size_id)
    JOIN item_side AS isd USING(item_side_id);
"""

trasaction_query = """
    SELECT 
        t.tr_id, i.item_name, isz.item_size, isd.item_side,
        tt.tr_type, t.tr_qty, t.before_qty, t.after_qty,
        u.user_name, t.tr_date
    FROM transactions AS t
    JOIN skus AS s USING(sku_id)
    JOIN items AS i USING(item_id)
    JOIN transaction_type AS tt USING(tr_type_id)
    JOIN item_size AS isz USING(item_size_id)
    JOIN item_side AS isd USING(item_side_id)
    JOIN users As u USING(user_id);
"""
