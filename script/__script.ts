import { MongoClient } from "mongodb";
import isEqual from "react-fast-compare";

const uri = `mongodb://ducdatpham:ducdat123@127.0.0.1:27017/?authSource=admin&readPreference=primary&serverSelectionTimeoutMS=2000&appname=MongoDB%20Compass&directConnection=true&ssl=false`;

const client = new MongoClient(uri);
client.connect();
const mongoDb = client.db("doffy");

const query = async () => {};

query();
