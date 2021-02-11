import jax
import jax.numpy as jnp
from jax import jit
from flax.core import FrozenDict

# JAX Compatible version of Catch bsuite environment. Source:
# https://github.com/deepmind/bsuite/blob/master/bsuite/environments/catch.py

# Default environment parameters
params_catch = {"max_steps_in_episode": 2000,}

rows = 10
columns = 5


def step(rng_input, params, state, action):
    """ Perform single timestep state transition. """
    # Sample new init state at each step and use only if there was a reset!
    ball_x, ball_y, paddle_x, paddle_y = sample_init_state(rng_input, params)
    prev_done = state[5]

    # Move the paddle + drop the ball.
    dx = action - 1  # [-1, 0, 1] = Left, no-op, right.
    paddle_x = (jnp.clip(state[2] + dx, 0, columns - 1)
                * (1-prev_done) + paddle_x * prev_done)
    ball_y = (state[1] + 1) * (1-prev_done) + ball_y * prev_done
    ball_x = state[0] * (1-prev_done) + ball_x * prev_done
    paddle_y = state[3] * (1-prev_done)  + paddle_y * prev_done

    # Rewrite reward as boolean multiplication
    done = (ball_y == paddle_y)
    catched = (paddle_x == ball_x)
    reward = done*(1*catched + -1*(1-catched))

    info = {}
    time = state[4] + 1
    state = jnp.array([ball_x, ball_y, paddle_x, paddle_y, time, done])
    return get_obs(state, params), state, reward, done, info


def sample_init_state(rng_input, params):
    """ Sample a new initial state. """
    high = jnp.zeros((rows, columns))
    ball_x = jax.random.randint(rng_input, shape=(),
                                minval=0, maxval=columns)
    ball_y = 0
    paddle_x = columns // 2
    paddle_y = rows - 1
    return ball_x, ball_y, paddle_x, paddle_y


def reset(rng_input, params):
    """ Reset environment state by sampling initial position. """
    ball_x, ball_y, paddle_x, paddle_y = sample_init_state(rng_input, params)
    # Last two state vector correspond to timestep and done
    state = jnp.array([ball_x, ball_y, paddle_x, paddle_y, 0, 0])
    return get_obs(state, params), state


def get_obs(state, params):
    """ Return observation from raw state trafo. """
    board = jnp.zeros((rows, columns))
    board = jax.ops.index_update(board, jax.ops.index[state[1], state[0]], 1.)
    board = jax.ops.index_update(board, jax.ops.index[state[3], state[2]], 1.)
    return board


reset_catch = jit(reset)
step_catch = jit(step)