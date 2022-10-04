import http from "http";
import { Server } from "socket.io";
import { SOCKET_EVENT } from "./enum";
import { TypeAuthenticate } from "./interface";
import { TypeAddComment } from "./interface/bubble";
import { TypeCreateChatTag, TypeHandleSeenMessage } from "./interface/chatTag";
import { TypeSendMessageRequest, TypeTyping } from "./interface/message";
import {
    addUserActive,
    getSocketIdOfListUserActive,
    getSocketIdOfUserId,
    putBackUserActive,
    putUserInBackground,
    removerUserActive,
} from "./services/assistant";
import { getMyListChatTagsAndMyId } from "./services/authentication";
import { addComment } from "./services/bubble";
import { handleSeenMessage, handleStartConversation } from "./services/chatTag";
import { handleSendMessage } from "./services/message";

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
            await addUserActive({
                userId: myId,
                socketId: socket.id,
            });
            // join all room of chat tag have in
            listMyConversations.forEach((item) => {
                socket.join(String(item._id));
            });
        } catch (err) {
            console.log("Error authenticate: ", err);
            socket.emit(SOCKET_EVENT.unauthorized);
        }
    });

    socket.on(SOCKET_EVENT.appActive, () => {
        putBackUserActive(socket.id);
    });
    socket.on(SOCKET_EVENT.appBackground, () => {
        putUserInBackground(socket.id);
    });

    /**
     * Bubble
     */
    socket.on(SOCKET_EVENT.addComment, async (params: TypeAddComment) => {
        try {
            const res = await addComment(params);
            io.to(params.comment.postId).emit(
                SOCKET_EVENT.addComment,
                res.socketComment
            );
            if (res.socketNotification) {
                io.to(res.socketNotification.receiverSocketId).emit(
                    SOCKET_EVENT.notification,
                    res.socketNotification.data
                );
            }
        } catch (err) {
            console.log("Err adding comment: ", err);
        }
    });

    socket.on(SOCKET_EVENT.leaveRoom, (bubbleId) => {
        console.log("Leave room: ", bubbleId);
        socket.leave(bubbleId);
    });

    /**
     * ChatTag
     */
    socket.on(SOCKET_EVENT.createChatTag, async (params: TypeCreateChatTag) => {
        try {
            const res = await handleStartConversation(params);
            if (res === undefined) {
                return;
            }
            const data: any = res.data;
            if (res.isExisted) {
                io.to(data.conversationId).emit(SOCKET_EVENT.message, res.data);
            } else if (!res.isExisted) {
                const listSocketIds = await getSocketIdOfListUserActive(
                    data.listUser.map((item: any) => item.id)
                );
                listSocketIds.forEach((socketId) => {
                    io.to(socketId).emit(SOCKET_EVENT.createChatTag, res.data);
                });
            }
        } catch (err) {
            console.log("Error when create chat tag: ", err);
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
                console.log("Error seen message: ", err);
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
            await removerUserActive(socket.id);
            /**
             * Leave room - you don't need because socketIO will do this for you
             */
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
            else if (url === "comment/delete-comment") {
                io.to(data.postId).emit(
                    SOCKET_EVENT.deleteComment,
                    data.commentId
                );
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
// startBotDiscord();

// console.log("Start node success");
