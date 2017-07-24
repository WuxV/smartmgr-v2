all: protoc

.PHONY:
protoc:
	protoc --proto_path=proto --python_out=. proto/pds.proto
	protoc --proto_path=proto --python_out=. proto/ios.proto
	protoc --proto_path=proto --python_out=. proto/mds.proto

.PHONY:
clean:
	rm -rf ./*_pb2.py
	rm -rf ./*.pyc
