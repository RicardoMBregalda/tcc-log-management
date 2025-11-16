package main

import (
	"context"
	"fmt"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type FlexTime struct {
	time.Time
}

type TestLog struct {
	ID        string                 `bson:"id"`
	Hash      string                 `bson:"hash"`
	Timestamp string                 `bson:"timestamp"`
	Source    string                 `bson:"source"`
	Level     string                 `bson:"level"`
	Message   string                 `bson:"message"`
	Metadata  map[string]interface{} `bson:"metadata,omitempty"`
	CreatedAt time.Time              `bson:"created_at"`
}

func main() {
	// Connect to MongoDB
	ctx := context.Background()
	client, err := mongo.Connect(ctx, options.Client().ApplyURI("mongodb://localhost:27017"))
	if err != nil {
		fmt.Printf("Failed to connect: %v\n", err)
		return
	}
	defer client.Disconnect(ctx)

	// Get collection
	coll := client.Database("logdb").Collection("logs")

	// Create test log
	log := TestLog{
		ID:        "test_" + time.Now().Format("20060102150405"),
		Hash:      "testhash123",
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Source:    "test-service-1",
		Level:     "INFO",
		Message:   "Test log from debug script",
		Metadata: map[string]interface{}{
			"test_id": 12345,
		},
		CreatedAt: time.Now().UTC(),
	}

	// Try to insert
	fmt.Printf("Attempting to insert log: %+v\n", log)
	result, err := coll.InsertOne(ctx, log)
	if err != nil {
		fmt.Printf("❌ INSERT FAILED: %v\n", err)
		fmt.Printf("Error type: %T\n", err)
		return
	}

	fmt.Printf("✅ INSERT SUCCESS! ID: %v\n", result.InsertedID)

	// Try to find it
	var found TestLog
	err = coll.FindOne(ctx, bson.M{"id": log.ID}).Decode(&found)
	if err != nil {
		fmt.Printf("❌ FIND FAILED: %v\n", err)
		return
	}

	fmt.Printf("✅ FOUND: %+v\n", found)
}
