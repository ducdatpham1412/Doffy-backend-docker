import { MongoClient } from "mongodb";

const uri = `mongodb://username:password@127.0.0.1:27017/?authSource=admin&readPreference=primary&serverSelectionTimeoutMS=2000&appname=MongoDB%20Compass&directConnection=true&ssl=false`;

const client = new MongoClient(uri);
client.connect();
const mongoDb = client.db("doffy");

const query = async () => {
    const all_posts = await mongoDb
        .collection("discovery_post")
        .find({}, { session: client.startSession() });

    all_posts.forEach((item) => {
        if (item.topic === null) {
            mongoDb.collection("discovery_post").updateOne(
                {
                    _id: item._id,
                },
                {
                    $set: {
                        topic: [],
                    },
                }
            );
        } else {
            mongoDb.collection("discovery_post").updateOne(
                {
                    _id: item._id,
                },
                {
                    $set: {
                        topic: [item.topic],
                    },
                }
            );
        }
    });
};

query();
