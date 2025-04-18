FROM node:16-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PORT=3456

# Expose the port the app runs on
EXPOSE 3456

# Command to run the application
CMD ["npm", "start"] 