package main

func setup() {
	r := gin.Default()

	r.GET("/health", healthHandler)
	r.HEAD("/health", headHandler)
	r.OPTIONS("/health", optionsHandler)
	r.POST("/users", createUser)
	r.PUT("/users/:id", updateUser)
	r.PATCH("/users/:id", patchUser)
	r.DELETE("/items/:id", deleteItem)

	api := r.Group("/api")
	api.GET("/users", listUsers)
	v1 := api.Group("/v1/")
	v1.GET("/health", versionedHealth)

	r.GET(dynamicPath, dynamicHandler)
	r.GET("/users/" + userID, dynamicHandler)
	dynamic := r.Group(prefix)
	dynamic.GET("/hidden", hiddenHandler)
	r.Handle("GET", "/unsupported", handler)

	// r.GET("/commented-out", ignoredHandler)
	/* api.POST("/also-commented-out", ignoredHandler) */
	example := `r.DELETE("/inside-a-string", ignoredHandler)`
	_ = example
}
