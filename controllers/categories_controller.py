import os
from bson import json_util, ObjectId
import json
from .recipe_controller import map_response


# this function is to query a single recipe from database
def single_recipe_controller(filters, db_conn, host_url):
    print("from single recipe...")
    print("filter :", filters)

    try:
        result = db_conn["recipes"].find(filters).sort("createdOn", -1)
        recipe_list = map_response(result, host_url)
        return recipe_list

    except Exception as e:
        print(e)
        return {"success": False, "message": "Error in api: " + str(e)}