
# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):

#         token = None

#         # 1️⃣ Read Authorization header
#         auth_header = request.headers.get("Authorization")

#         if auth_header and auth_header.startswith("Bearer "):
#             token = auth_header.split(" ")[1]

#         if not token:
#             return jsonify({
#                 "success": False,
#                 "message": "Token is missing"
#             }), 401

#         try:
#             # 2️⃣ Decode token
#             decoded = jwt.decode(
#                 token,
#                 app.config["SECRET_KEY"],
#                 algorithms=["HS256"]
#             )

#             # 3️⃣ Attach user_id to request
#             request.user_id = decoded["user_id"]

#         except jwt.ExpiredSignatureError:
#             return jsonify({
#                 "success": False,
#                 "message": "Token expired"
#             }), 401

#         except jwt.InvalidTokenError:
#             return jsonify({
#                 "success": False,
#                 "message": "Invalid token"
#             }), 401

#         # 4️⃣ Token valid → allow request
#         return f(*args, **kwargs)

#     return decorated






# //////////////

# @app.route("/history/<int:id>/pdf-name", methods=["PATCH"])
# def edit_pdf_name(id):
#     # 1️⃣ Fetch report
#     report = Report.query.get(id)

#     if not report:
#         return jsonify({
#             "success": False,
#             "message": "Report not found"
#         }), 404

#     # 2️⃣ Read input
#     data = request.json
#     new_name = data.get("pdf_name")

#     # 3️⃣ Validation
#     if not new_name or not new_name.strip():
#         return jsonify({
#             "success": False,
#             "message": "PDF name cannot be empty"
#         }), 400

#     # Force .pdf extension
#     if not new_name.lower().endswith(".pdf"):
#         new_name += ".pdf"

#     # 4️⃣ Update DB
#     report.pdf_name = new_name

#     try:
#         db.session.commit()
#     except Exception:
#         db.session.rollback()
#         return jsonify({
#             "success": False,
#             "message": "Failed to update PDF name"
#         }), 500

#     # 5️⃣ Response
#     return jsonify({
#         "success": True,
#         "message": "PDF name updated successfully",
#         "data": {
#             "id": report.id,
#             "pdf_name": report.pdf_name
#         }
#     })