import React from 'react';
import { Typography, Box, Paper, Grid } from '@mui/material';
import { Link } from 'react-router-dom';

const Home: React.FC = () => {
  return (
    <Box>
      <Typography variant="h3" component="h1" gutterBottom>
        Welcome to Grabarr
      </Typography>
      <Typography variant="h5" color="text.secondary" paragraph>
        Manage your Sonarr instances and optimize search operations
      </Typography>
      
      <Grid container spacing={3} sx={{ mt: 4 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Instance Management
            </Typography>
            <Typography paragraph>
              Add, configure, and manage multiple Sonarr instances from a single interface.
            </Typography>
            <Link to="/instances" style={{ textDecoration: 'none' }}>
              Manage Instances
            </Link>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Search Optimization
            </Typography>
            <Typography paragraph>
              Queue and optimize searches across your instances for better performance.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Home; 