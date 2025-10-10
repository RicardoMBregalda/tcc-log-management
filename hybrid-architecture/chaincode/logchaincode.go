package main

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract provides functions for managing logs
type SmartContract struct {
	contractapi.Contract
}

// Log describes the structure of a log entry
type Log struct {
	ID        string    `json:"id"`
	Hash      string    `json:"hash"`
	Timestamp time.Time `json:"timestamp"`
	Source    string    `json:"source"`
	Level     string    `json:"level"`
	Message   string    `json:"message"`
	Metadata  string    `json:"metadata"`
}

// CreateLog creates a new log entry in the ledger
func (s *SmartContract) CreateLog(ctx contractapi.TransactionContextInterface, id string, hash string, timestamp string, source string, level string, message string, metadata string) error {
	exists, err := s.LogExists(ctx, id)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("the log %s already exists", id)
	}

	parsedTime, err := time.Parse(time.RFC3339, timestamp)
	if err != nil {
		return fmt.Errorf("invalid timestamp format: %v", err)
	}

	log := Log{
		ID:        id,
		Hash:      hash,
		Timestamp: parsedTime,
		Source:    source,
		Level:     level,
		Message:   message,
		Metadata:  metadata,
	}

	logJSON, err := json.Marshal(log)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(id, logJSON)
}

// QueryLog returns the log entry with the given ID
func (s *SmartContract) QueryLog(ctx contractapi.TransactionContextInterface, id string) (*Log, error) {
	logJSON, err := ctx.GetStub().GetState(id)
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if logJSON == nil {
		return nil, fmt.Errorf("the log %s does not exist", id)
	}

	var log Log
	err = json.Unmarshal(logJSON, &log)
	if err != nil {
		return nil, err
	}

	return &log, nil
}

// LogExists returns true when log with given ID exists in world state
func (s *SmartContract) LogExists(ctx contractapi.TransactionContextInterface, id string) (bool, error) {
	logJSON, err := ctx.GetStub().GetState(id)
	if err != nil {
		return false, fmt.Errorf("failed to read from world state: %v", err)
	}

	return logJSON != nil, nil
}

// GetAllLogs returns all logs found in world state
func (s *SmartContract) GetAllLogs(ctx contractapi.TransactionContextInterface) ([]*Log, error) {
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var logs []*Log
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var log Log
		err = json.Unmarshal(queryResponse.Value, &log)
		if err != nil {
			return nil, err
		}
		logs = append(logs, &log)
	}

	return logs, nil
}

// GetLogHistory returns the history of a log entry
func (s *SmartContract) GetLogHistory(ctx contractapi.TransactionContextInterface, id string) ([]HistoryQueryResult, error) {
	resultsIterator, err := ctx.GetStub().GetHistoryForKey(id)
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var records []HistoryQueryResult
	for resultsIterator.HasNext() {
		response, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var log Log
		if len(response.Value) > 0 {
			err = json.Unmarshal(response.Value, &log)
			if err != nil {
				return nil, err
			}
		}

		timestamp := time.Unix(response.Timestamp.Seconds, int64(response.Timestamp.Nanos)).String()

		record := HistoryQueryResult{
			TxId:      response.TxId,
			Timestamp: timestamp,
			IsDelete:  response.IsDelete,
			Log:       log,
		}
		records = append(records, record)
	}

	return records, nil
}

// HistoryQueryResult structure for history queries
type HistoryQueryResult struct {
	TxId      string `json:"txId"`
	Timestamp string `json:"timestamp"`
	IsDelete  bool   `json:"isDelete"`
	Log       Log    `json:"log"`
}

// QueryLogsByLevel returns logs with the specified level
func (s *SmartContract) QueryLogsByLevel(ctx contractapi.TransactionContextInterface, level string) ([]*Log, error) {
	queryString := fmt.Sprintf(`{"selector":{"level":"%s"}}`, level)
	return s.getQueryResultForQueryString(ctx, queryString)
}

// QueryLogsBySource returns logs from the specified source
func (s *SmartContract) QueryLogsBySource(ctx contractapi.TransactionContextInterface, source string) ([]*Log, error) {
	queryString := fmt.Sprintf(`{"selector":{"source":"%s"}}`, source)
	return s.getQueryResultForQueryString(ctx, queryString)
}

// getQueryResultForQueryString executes the passed in query string
func (s *SmartContract) getQueryResultForQueryString(ctx contractapi.TransactionContextInterface, queryString string) ([]*Log, error) {
	resultsIterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var logs []*Log
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var log Log
		err = json.Unmarshal(queryResponse.Value, &log)
		if err != nil {
			return nil, err
		}
		logs = append(logs, &log)
	}

	return logs, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		fmt.Printf("Error creating log chaincode: %v", err)
		return
	}

	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting log chaincode: %v", err)
	}
}
