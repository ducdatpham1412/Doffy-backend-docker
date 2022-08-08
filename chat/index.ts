import http from "http";
import { Server } from "socket.io";
import { SOCKET_EVENT } from "./enum";
import { TypeAuthenticate } from "./interface";
import { TypeHandleSeenMessage } from "./interface/chatTag";
import { TypeSendMessageRequest, TypeTyping } from "./interface/message";
import mongoDb from "./mongoDb";
import {
    getSocketIdOfListUserActive,
    getSocketIdOfUserId,
} from "./services/assistant";
import { getMyListChatTagsAndMyId } from "./services/authentication";
import { addComment } from "./services/bubble";
import { handleSeenMessage, handleStartNewChatTag } from "./services/chatTag";
import { startBotDiscord } from "./services/discord";
import { handleSendMessage } from "./services/message";
import Static from "./static";

const httpServer = http.createServer();
const io = new Server(httpServer, {
    pingTimeout: 60000,
    pingInterval: 25000,
});

// const enjoyModeRoom = "enjoy-mode-room";

io.on("connection", (socket) => {
    console.log("\n\nSocket connect with: ", socket.id);

    /**
     * Authenticate
     */
    socket.on(SOCKET_EVENT.authenticate, async (params: TypeAuthenticate) => {
        try {
            const { listMyConversations, myId } =
                await getMyListChatTagsAndMyId(params.token);
            // save to user active
            await mongoDb.collection("userActive").deleteMany({ userId: myId });
            await mongoDb.collection("userActive").insertOne({
                userId: myId,
                socketId: socket.id,
            });
            Static.addUserActive({
                userId: myId,
                socketId: socket.id,
            });
            // join all room of chat tag have in
            listMyConversations.forEach((item) => {
                socket.join(String(item._id));
            });
        } catch (err) {
            console.log("Error authenticate: ", socket.id);
            socket.emit(SOCKET_EVENT.unauthorized);
        }
    });

    socket.on(SOCKET_EVENT.appActive, () => {
        Static.putBackActive(socket.id);
    });
    socket.on(SOCKET_EVENT.appBackground, () => {
        Static.putInBackground(socket.id);
    });

    /**
     * Bubble
     */
    socket.on(SOCKET_EVENT.addComment, async (params) => {
        try {
            const res = await addComment(params);
            io.to(params.bubbleId).emit(SOCKET_EVENT.addComment, res.data);
        } catch (err) {
            console.log("Err adding comment: ", socket.id);
        }
    });

    socket.on(SOCKET_EVENT.leaveRoom, (bubbleId) => {
        console.log("Leave room: ", bubbleId);
        socket.leave(bubbleId);
    });

    /**
     * ChatTag
     */
    socket.on(SOCKET_EVENT.createChatTag, async (params) => {
        try {
            const res = await handleStartNewChatTag(params);
            // If chat tag existed, only send message to user
            if (res?.isChatTagExisted) {
                io.to(res?.response?.chatTag).emit(
                    SOCKET_EVENT.message,
                    res.response
                );
                return;
            }

            if (res?.response?.listUser && res.dataNotification) {
                const listSocketId = await getSocketIdOfListUserActive(
                    res?.response?.listUser?.map((item: any) => item.id)
                );

                listSocketId.forEach((socketId) => {
                    io.to(socketId).emit(
                        SOCKET_EVENT.createChatTag,
                        res.response
                    );
                    socket
                        .to(socketId)
                        .emit(SOCKET_EVENT.notification, res.dataNotification);
                });
            }
        } catch (err) {
            console.log("Error when create chat tag: ", socket.id);
        }
    });
    // after receive socket "createChatTag" in client, join room of that chat tag
    socket.on(SOCKET_EVENT.joinRoom, (conversationId: string) => {
        console.log("join room: ", conversationId);
        socket.join(conversationId);
    });

    socket.on(
        SOCKET_EVENT.seenMessage,
        async (params: TypeHandleSeenMessage) => {
            try {
                const res = await handleSeenMessage(params);
                if (res) {
                    io.to(params.conversationId).emit(
                        SOCKET_EVENT.seenMessage,
                        res
                    );
                }
            } catch (err) {
                console.log("Error seen message: ", socket.id);
            }
        }
    );

    /**
     * Message
     */
    socket.on(SOCKET_EVENT.message, async (params: TypeSendMessageRequest) => {
        const res = await handleSendMessage(params);
        io.to(res.conversationId).emit(SOCKET_EVENT.message, res);
    });
    socket.on(SOCKET_EVENT.typing, (params: TypeTyping) => {
        io.to(params.conversationId).emit(SOCKET_EVENT.typing, params);
    });
    socket.on(SOCKET_EVENT.unTyping, (params: TypeTyping) => {
        io.to(params.conversationId).emit(SOCKET_EVENT.unTyping, params);
    });

    /**
     * Disconnect
     */
    socket.on("disconnect", async (reason) => {
        try {
            console.log(`Disconnected: ${socket.id}\nReason: `, reason);

            await mongoDb
                .collection("userActive")
                .findOneAndDelete({ socketId: socket.id });
            /**
             * Leave room - you don't need because socketIO will do this for you
             */
            Static.removeUserActive(socket.id);
        } catch (err) {
            console.log("Error disconnect: ", socket.id);
        }
    });
});

httpServer.listen(3000);

/**
 * This for request http from app
 */
const listenAppServer = http.createServer(async (req, res) => {
    const url = req.url;

    if (req.method === "POST") {
        let dataString = "";
        req.on("data", (chunk) => {
            dataString += chunk;
        });

        req.on("end", async () => {
            const data = JSON.parse(dataString);

            /**
             * NOTIFICATION
             */

            // Like post
            if (url === "/notification/like-post") {
                const socketId = await getSocketIdOfUserId(data.receiver);
                if (socketId) {
                    io.to(socketId).emit(SOCKET_EVENT.notification, data.data);
                }
            }

            // Follow
            else if (url === "/notification/follow") {
                const socketId = await getSocketIdOfUserId(data.receiver);
                if (socketId) {
                    io.to(socketId).emit(SOCKET_EVENT.notification, data.data);
                }
            }

            // Comment
            else if (url === "/notification/comment") {
                const socketId = await getSocketIdOfUserId(data.receiver);
                if (socketId) {
                    io.to(socketId).emit(SOCKET_EVENT.notification, data.data);
                }
            }

            // New chat-tag from create group
            else if (url === "/new-chat-tag") {
                const socketId = await getSocketIdOfUserId(data.receiver);
                if (socketId) {
                    io.to(socketId).emit(SOCKET_EVENT.createChatTag, data.data);
                }
            }

            // Block, unblock user
            else if (url === "/setting/block") {
                if (data.conversationId) {
                    io.to(data.conversationId).emit(
                        SOCKET_EVENT.isBlocked,
                        data.conversationId
                    );
                }
            } else if (url === "/setting/unblock") {
                if (data.conversationId) {
                    io.to(data.conversationId).emit(
                        SOCKET_EVENT.unBlocked,
                        data.conversationId
                    );
                }
            }

            // Stop, open conversation
            else if (url === "/setting/stop-conversation") {
                if (data.conversationId) {
                    io.to(data.conversationId).emit(
                        SOCKET_EVENT.stopConversation,
                        data.conversationId
                    );
                }
            } else if (url === "/setting/open-conversation") {
                if (data.conversationId) {
                    io.to(data.conversationId).emit(
                        SOCKET_EVENT.openConversation,
                        data.conversationId
                    );
                }
            }

            // Change conversation name, color
            else if (url === "/chat/change-chat-name") {
                if (data) {
                    io.to(data.conversationId).emit(
                        SOCKET_EVENT.changeChatName,
                        {
                            conversationId: data.conversationId,
                            name: data.name,
                        }
                    );
                    io.to(data.conversationId).emit(
                        SOCKET_EVENT.message,
                        data.newMessage
                    );
                }
            } else if (url === "/chat/change-chat-color") {
                if (data) {
                    io.to(data.conversationId).emit(
                        SOCKET_EVENT.changeChatColor,
                        {
                            conversationId: data.conversationId,
                            color: data.color,
                        }
                    );
                    io.to(data.conversationId).emit(
                        SOCKET_EVENT.message,
                        data.newMessage
                    );
                }
            } else if (url === "/chat/delete-message") {
                if (data) {
                    io.to(data.conversationId).emit(
                        SOCKET_EVENT.deleteMessage,
                        data
                    );
                }
            }

            res.end();
        });
    } else {
        res.end("Null");
    }
});
listenAppServer.listen(1412);

/**
 * This is for discord bot
 */
startBotDiscord();

console.log("Start node success");

// socket.on(SOCKET_EVENT.joinCommunity, async (params) => {
//     try {
//         const chatTagId = await joinCommunity(params);
//         io.to(socket.id).emit(SOCKET_EVENT.joinCommunity, chatTagId);
//         io.to(chatTagId).emit(
//             SOCKET_EVENT.hadNewUserJoinCommunity,
//             chatTagId
//         );
//         socket.join(chatTagId);
//     } catch (err) {
//         console.log("Err join community: ", err);
//     }
// });
