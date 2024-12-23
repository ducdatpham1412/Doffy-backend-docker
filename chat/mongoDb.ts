import { MongoClient } from "mongodb";
import env from "./env";

const uri = `mongodb://${env.MONGO_USER}:${env.MONGO_PASSWORD}@${env.MONGO_HOST}:27017/?authSource=admin&readPreference=primary&serverSelectionTimeoutMS=15000&appname=MongoDB%20Compass&directConnection=true&ssl=false`;

const client = new MongoClient(uri);
client.connect();
const mongoDb = client.db("doffy");

export default mongoDb;
