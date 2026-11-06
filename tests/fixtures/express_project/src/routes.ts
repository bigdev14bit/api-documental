import express from "express";

const app = express();
const router = express.Router();

app.get("/health", healthHandler);
router.post("/users", createUser);
router.put("/users/:userId", updateUser);
router.patch("/users/:userId", patchUser);

app.route("/items")
  .get(listItems)
  .post(createItem)
  .delete(deleteItem);

app.get(`/version`, versionHandler);
app.get(`/users/${userId}`, dynamicHandler);
app.get(dynamicPath, unresolvedHandler);

// app.get("/commented-out", ignoredHandler);
/* router.delete("/also-commented-out", ignoredHandler); */
const example = "router.delete('/inside-a-string', ignoredHandler)";
const routePattern = /app.get("not-a-route")/;
const divided = routePattern / 2;
